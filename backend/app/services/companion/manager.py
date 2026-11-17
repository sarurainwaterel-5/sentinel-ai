"""Bounded deterministic rendering beside, never replacing, closed model release."""
import time
import re
from typing import Protocol
from app.services.sre.contracts import SREError

class ConversationProvider(Protocol):
    """Future approved provider; generated text remains untrusted and withheld."""
    def generate(self, *, question: str, context: list, facts: list) -> str: ...

class ConversationManager:
    def __init__(self,store,knowledge,*,provider=None,clock=time.monotonic):
        self.store=store;self.knowledge=knowledge;self.provider=provider;self.clock=clock
    def turn(self,access,t,a,id,*,now,turn_id,text,expected_revision,cancelled=lambda:False):
        start=self.clock()
        def checkpoint():
            self.store.authority.check(access,t,a,'converse')
            if cancelled():raise SREError('REQUEST_CANCELLED')
            if self.clock()-start>3:raise SREError('REQUEST_TIMEOUT')
        checkpoint()
        if type(text) is not str or not text.strip() or len(text)>4000:raise SREError('INVALID_MESSAGE')
        history=self.store.get(access,t,a,id,now=now)
        previous=[m for m in history['messages'] if m['role']=='user'][-6:]
        def followup(value):
            lower=value.lower()
            return bool(set(re.findall(r'[a-z]+',lower)) & {'more','that','those','it'}) and len(value.split())<8 or lower.strip(' ?!.') in {'why','explain'}
        question=text
        if followup(text):
            substantive=[message for message in previous if not followup(message['content'])]
            if not substantive:
                response={'content':'I need a topic or an explicitly selected incident to answer that follow-up.','sources':[],'status':'INSUFFICIENT_CONTEXT','topic':'missing context'}
                checkpoint();return self.store.append(access,t,a,id,now=now,turn_id=turn_id,text=text,expected_revision=expected_revision,response=response)
            question=(substantive[-1]['content']+' '+text)[:8000]
        # User instructions are question data; no tools, arbitrary paths or memory writes.
        facts=self.knowledge.retrieve(question,max_items=6);checkpoint()
        sources=[];lines=[]
        for fact in facts:
            lines.append(fact['text']+' Implementation: '+fact['implementation_status']+'. Authorization: '+fact['authorization_status']+'. Verification: '+fact['verification_status']+'.')
            for citation in fact['citations']:
                source={'source_id':citation['source_id'],'label':citation['path'],'path':citation['path'],'sha256':citation['sha256']}
                if source not in sources:sources.append(source)
        status='REPOSITORY_RECORDS' if lines else 'INSUFFICIENT_EVIDENCE'
        content='\n\n'.join(lines) if lines else 'I do not have verified repository evidence for that question. Select an authorized incident for operational investigation. Live conversational inference is unavailable.'
        if self.provider is not None:
            # Compatibility seam only. Never execute an unapproved provider or publish its prose.
            content+='\n\nGenerated model prose is withheld by the existing governed release boundary.'
        if history['tone']=='friendly':content='Here is what I can establish from the available records.\n\n'+content
        response={'content':content,'sources':sources,'status':status,'topic':facts[0]['capability_id'] if facts else 'unknown'}
        checkpoint()
        return self.store.append(access,t,a,id,now=now,turn_id=turn_id,text=text,expected_revision=expected_revision,response=response)
