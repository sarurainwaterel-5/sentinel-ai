export default function RecentMissions({ missions = [], onSelect }) {
  return <section className="panel"><h2>Recent Missions</h2><p className="muted">Latest 20 teaching missions in the selected context. Existing PDFs imported before mission tracking remain in the catalog.</p>
    {missions.length ? <ul className="workspace-list">{missions.map((mission) => <li key={mission.id}><button className="secondary-action" onClick={() => onSelect(mission)}>{mission.filename}</button><p>{mission.domain_id} · {mission.status} · {new Date(mission.created_at).toLocaleString()}</p></li>)}</ul> : <p>No teaching missions recorded in this context yet.</p>}
  </section>;
}
