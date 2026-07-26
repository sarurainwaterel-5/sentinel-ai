/**
 * Domain Provider
 *
 * The Domain Provider preserves one shared domain context across
 * SentinelAI's frontend workspaces.
 *
 * The backend remains the source of truth for canonical domains.
 *
 * The frontend preserves the human's active workspace selection.
 */

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from 'react'

import { getDomainModel } from '../services/domainService'
import { DomainContext } from './domainContext'


const ALL_DOMAINS_ID = 'all'


function normalizeDomain(domain, source) {
  if (!domain) {
    return null
  }

  return {
    id: domain.domain_id ?? domain.id,
    name: domain.name ?? domain.title ?? 'Unnamed Domain',
    description: domain.description ?? '',
    kind: domain.kind ?? 'unknown',
    status: domain.status ?? 'unknown',
    owner: domain.owner ?? null,
    source,
    evidence: domain.evidence ?? [],
    evidenceCount:
      domain.evidence_count ??
      domain.document_count ??
      domain.evidence?.length ??
      0,
  }
}


function normalizeDomainModel(domainModelResponse) {
  const systemDomains = Array.isArray(
    domainModelResponse?.system_domains,
  )
    ? domainModelResponse.system_domains.map((domain) =>
        normalizeDomain(domain, 'system'),
      )
    : []

  const userDomains = Array.isArray(
    domainModelResponse?.user_domains,
  )
    ? domainModelResponse.user_domains.map((domain) =>
        normalizeDomain(domain, 'user'),
      )
    : []

  return [
    ...systemDomains,
    ...userDomains,
  ].filter((domain) => domain?.id)
}


export function DomainProvider({ children }) {
  const [domainModel, setDomainModel] = useState(null)
  const [availableDomains, setAvailableDomains] = useState([])

  const [activeDomainId, setActiveDomainId] = useState(
    () =>
      localStorage.getItem('sentinel.activeDomainId') ??
      ALL_DOMAINS_ID,
  )

  const [isLoadingDomains, setIsLoadingDomains] = useState(true)
  const [domainError, setDomainError] = useState(null)
  const [refreshVersion, setRefreshVersion] = useState(0)

  useEffect(() => {
    let cancelled = false

    getDomainModel()
      .then((domainModelResponse) => {
        if (cancelled) {
          return
        }

        setDomainModel(domainModelResponse)
        setAvailableDomains(
          normalizeDomainModel(domainModelResponse),
        )
        setDomainError(null)
      })
      .catch((error) => {
        if (cancelled) {
          return
        }

        console.error(
          'Unable to load Sentinel domains:',
          error,
        )

        setDomainError(
          error instanceof Error
            ? error.message
            : 'Unable to load domains.',
        )
      })
      .finally(() => {
        if (!cancelled) {
          setIsLoadingDomains(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [refreshVersion])

  const effectiveActiveDomainId = useMemo(() => {
    if (activeDomainId === ALL_DOMAINS_ID) {
      return ALL_DOMAINS_ID
    }

    const activeDomainExists = availableDomains.some(
      (domain) => domain.id === activeDomainId,
    )

    return activeDomainExists
      ? activeDomainId
      : ALL_DOMAINS_ID
  }, [activeDomainId, availableDomains])

  useEffect(() => {
    localStorage.setItem(
      'sentinel.activeDomainId',
      effectiveActiveDomainId,
    )
  }, [effectiveActiveDomainId])

  const activeDomain = useMemo(() => {
    if (effectiveActiveDomainId === ALL_DOMAINS_ID) {
      return {
        id: ALL_DOMAINS_ID,
        name: 'All Domains',
        description: 'Explicit cross-domain workspace',
        kind: 'cross-domain',
        status: 'active',
        source: 'frontend',
        evidence: [],
        evidenceCount: availableDomains.reduce(
          (total, domain) =>
            total + domain.evidenceCount,
          0,
        ),
      }
    }

    return (
      availableDomains.find(
        (domain) =>
          domain.id === effectiveActiveDomainId,
      ) ?? null
    )
  }, [availableDomains, effectiveActiveDomainId])

  const selectDomain = useCallback(
    (domainId) => {
      if (!domainId) {
        return
      }

      const isKnownDomain =
        domainId === ALL_DOMAINS_ID ||
        availableDomains.some(
          (domain) => domain.id === domainId,
        )

      if (!isKnownDomain) {
        console.warn(
          `Unable to select unknown domain '${domainId}'.`,
        )
        return
      }

      setActiveDomainId(domainId)
    },
    [availableDomains],
  )

  const refreshDomains = useCallback(() => {
    setIsLoadingDomains(true)
    setRefreshVersion((version) => version + 1)
  }, [])

  const value = useMemo(
    () => ({
      activeDomain,
      activeDomainId: effectiveActiveDomainId,
      availableDomains,
      domainModel,
      domainError,
      isCrossDomain:
        effectiveActiveDomainId === ALL_DOMAINS_ID,
      isLoadingDomains,
      refreshDomains,
      selectDomain,
    }),
    [
      activeDomain,
      availableDomains,
      domainModel,
      domainError,
      effectiveActiveDomainId,
      isLoadingDomains,
      refreshDomains,
      selectDomain,
    ],
  )

  return (
    <DomainContext.Provider value={value}>
      {children}
    </DomainContext.Provider>
  )
}
