import { useContext } from 'react'

import { DomainContext } from './domainContext'


export function useDomain() {
  const context = useContext(DomainContext)

  if (!context) {
    throw new Error(
      'useDomain must be used inside a DomainProvider.',
    )
  }

  return context
}
