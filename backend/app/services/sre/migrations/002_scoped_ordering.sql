CREATE INDEX sre_observations_by_service_time ON sre_observations(tenant,app,service,source_time,id);
CREATE INDEX sre_dependencies_by_dependent ON sre_dependencies(tenant,app,dependent,source);
CREATE INDEX sre_incidents_by_service ON sre_incidents(tenant,app,service,id);
