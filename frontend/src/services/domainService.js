import { workspaceRequest } from "./workspaceApi";

export async function getDomainModel() {
  const model = await workspaceRequest("/domains");
  if (
    !Array.isArray(model.system_domains) ||
    !Array.isArray(model.user_domains) ||
    !model.summary ||
    !Array.isArray(model.validation?.checks)
  ) {
    throw new Error(
      "Sentinel returned an incomplete domain registry. Retry after checking Systems.",
    );
  }
  return model;
}

export async function getDomain(domainId) {
  return workspaceRequest(`/domains/${encodeURIComponent(domainId)}`);
}
