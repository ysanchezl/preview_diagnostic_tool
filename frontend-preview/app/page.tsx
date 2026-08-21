"use client";

import {
  AlertCircle,
  ArrowRight,
  BarChart3,
  Bot,
  BriefcaseBusiness,
  CalendarCheck,
  CheckCircle2,
  ClipboardList,
  Ear,
  FileText,
  Gauge,
  Globe,
  Loader2,
  MessagesSquare,
  Network,
  RefreshCw,
  Send,
  ShieldCheck,
  Sparkles,
  Workflow,
} from "lucide-react";
import { FormEvent, useMemo, useState } from "react";

type BusinessType =
  | "law_firm"
  | "dental_clinic"
  | "notary"
  | "gestoria"
  | "real_estate"
  | "ecommerce"
  | "professional_services"
  | "change_management_consulting"
  | "other";

type DiagnosticPayload = {
  company_name: string;
  business_type: BusinessType | "";
  employee_count: number;
  automation_goal: string;
  pain_points: string[];
  current_tools: string[];
  preferred_contact: "email" | "phone" | "whatsapp" | "not_specified";
};

type AutomationOpportunity = {
  problema_detectado: string;
  solucion_propuesta: string;
  beneficio_operativo: string;
  impacto_estimado: string;
  dificultad: "baja" | "media" | "alta";
  tipo: "quick_win" | "medio_plazo" | "avanzado";
};

type FlowStep = {
  id: string;
  title: string;
  short_description: string;
  step_type:
    | "start"
    | "input"
    | "process"
    | "automation"
    | "validation"
    | "communication"
    | "decision"
    | "reporting"
    | "end";
  owner: "client" | "automation" | "team" | "system";
  inputs: string[];
  outputs: string[];
  suggested_icon: string;
  estimated_impact: string;
};

type DiagnosticResponse = {
  company_name: string;
  business_type: BusinessType;
  executive_summary: string;
  recommended_automation: string;
  automations: AutomationOpportunity[];
  flow: FlowStep[];
  roi: {
    headline: string;
    assumptions: string[];
    benefits: string[];
  };
  implementation_phases: string[];
  contact_cta: string;
  disclaimer: string;
  provider: string;
};

type ProposalGenerationError = {
  proposal_ok: false;
  error_reason: string;
};

function isProposalError(
  data: DiagnosticResponse | ProposalGenerationError,
): data is ProposalGenerationError {
  return (data as ProposalGenerationError).proposal_ok === false;
}

type WebsiteEnrichmentResponse = {
  suggested_company_name: string | null;
  suggested_business_type: BusinessType | null;
  suggested_current_tools: string[];
  candidate_pain_points: string[];
  candidate_objectives: string | null;
  confidence: Record<string, "high" | "medium" | "low">;
  source_url: string;
  scraped_ok: boolean;
  error_reason: string | null;
};

type SuggestedField = "company_name" | "business_type" | "current_tools" | "pain_points" | "automation_goal";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const businessTypes: Array<{ value: BusinessType; label: string }> = [
  { value: "law_firm", label: "Bufete de abogados" },
  { value: "dental_clinic", label: "Clinica dental" },
  { value: "notary", label: "Notaria" },
  { value: "gestoria", label: "Gestoria / asesoria" },
  { value: "real_estate", label: "Inmobiliaria" },
  { value: "ecommerce", label: "Ecommerce" },
  { value: "professional_services", label: "Servicios profesionales" },
  { value: "change_management_consulting", label: "Consultoria en gestion del cambio e innovacion" },
  { value: "other", label: "Otro negocio" },
];

const iconMap = {
  "messages-square": MessagesSquare,
  ear: Ear,
  workflow: Workflow,
  bot: Bot,
  "chart-no-axes-combined": BarChart3,
  "calendar-check": CalendarCheck,
  "file-text": FileText,
  "shield-check": ShieldCheck,
  network: Network,
  default: Sparkles,
};

const initialPayload: DiagnosticPayload = {
  company_name: "",
  business_type: "",
  employee_count: 0,
  automation_goal: "",
  pain_points: [],
  current_tools: [],
  preferred_contact: "not_specified",
};

const FIELD_LABELS: Record<string, string> = {
  company_name: "Empresa",
  business_type: "Negocio",
  employee_count: "Empleados",
  automation_goal: "Objetivo",
  pain_points: "Pain points",
  current_tools: "Herramientas actuales",
  preferred_contact: "Contacto",
};

type ValidationError = {
  loc?: Array<string | number>;
  msg?: string;
  type?: string;
  ctx?: Record<string, unknown>;
};

function friendlyValidationMessage(errors: ValidationError[]): string {
  return errors
    .map((err) => {
      const field = String(err.loc?.[err.loc.length - 1] ?? "");
      const label = FIELD_LABELS[field] ?? field;
      const maxLength = err.ctx?.max_length;
      const minLength = err.ctx?.min_length;

      if (err.type === "too_long") return `${label}: maximo ${maxLength} elementos.`;
      if (err.type === "too_short") return `${label}: minimo ${minLength} elemento(s).`;
      if (err.type === "string_too_long") return `${label}: maximo ${maxLength} caracteres.`;
      if (err.type === "string_too_short") return `${label}: minimo ${minLength} caracteres.`;
      return `${label}: ${err.msg ?? "valor invalido"}.`;
    })
    .join(" ");
}

async function extractErrorMessage(response: Response, fallback: string): Promise<string> {
  const text = await response.text();
  try {
    const parsed = JSON.parse(text);
    if (typeof parsed.detail === "string") return parsed.detail;
    if (Array.isArray(parsed.detail)) return friendlyValidationMessage(parsed.detail);
  } catch {
    // Respuesta no era JSON: se usa el texto plano o el fallback.
  }
  return text || fallback;
}

function splitLines(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function IconForStep({ name }: { name: string }) {
  const Icon = iconMap[name as keyof typeof iconMap] ?? iconMap.default;
  return <Icon size={19} strokeWidth={2.2} />;
}

export default function Home() {
  const [payload, setPayload] = useState<DiagnosticPayload>(initialPayload);
  const [painPointsText, setPainPointsText] = useState(initialPayload.pain_points.join("\n"));
  const [toolsText, setToolsText] = useState(initialPayload.current_tools.join("\n"));
  const [employeeCountText, setEmployeeCountText] = useState("");
  const [proposal, setProposal] = useState<DiagnosticResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const [websiteUrl, setWebsiteUrl] = useState("");
  const [allowScraping, setAllowScraping] = useState(false);
  const [isEnriching, setIsEnriching] = useState(false);
  const [enrichError, setEnrichError] = useState("");
  const [suggestedFields, setSuggestedFields] = useState<Set<SuggestedField>>(new Set());
  const [candidatePainPoints, setCandidatePainPoints] = useState<string[]>([]);
  const [selectedCandidates, setSelectedCandidates] = useState<Set<string>>(new Set());
  const [candidateObjective, setCandidateObjective] = useState<string | null>(null);

  function clearSuggestion(field: SuggestedField) {
    setSuggestedFields((current) => {
      if (!current.has(field)) return current;
      const next = new Set(current);
      next.delete(field);
      return next;
    });
  }

  function toggleCandidatePainPoint(point: string) {
    setSelectedCandidates((current) => {
      const next = new Set(current);
      if (next.has(point)) next.delete(point);
      else next.add(point);
      return next;
    });
  }

  function addSelectedCandidatePainPoints() {
    const toAdd = candidatePainPoints.filter((point) => selectedCandidates.has(point));
    if (toAdd.length > 0) {
      setPainPointsText((current) => {
        const existing = splitLines(current);
        const merged = [...existing, ...toAdd.filter((point) => !existing.includes(point))];
        return merged.join("\n");
      });
      setSuggestedFields((current) => new Set(current).add("pain_points"));
    }
    setCandidatePainPoints([]);
    setSelectedCandidates(new Set());
  }

  function useCandidateObjective() {
    if (!candidateObjective) return;
    setPayload((current) => ({ ...current, automation_goal: candidateObjective }));
    setSuggestedFields((current) => new Set(current).add("automation_goal"));
    setCandidateObjective(null);
  }

  function dismissCandidates() {
    setCandidatePainPoints([]);
    setSelectedCandidates(new Set());
    setCandidateObjective(null);
  }

  async function handleEnrichWebsite() {
    if (!websiteUrl || !allowScraping) return;
    setEnrichError("");
    dismissCandidates();
    setIsEnriching(true);

    try {
      const response = await fetch(`${API_URL}/api/v1/diagnostics/enrich`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ website_url: websiteUrl, allow_scraping: allowScraping }),
      });

      if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "No se pudo analizar la web."));
      }

      const data = (await response.json()) as WebsiteEnrichmentResponse;

      if (!data.scraped_ok) {
        const messages: Record<string, string> = {
          timeout: "El analisis tardo demasiado, intenta de nuevo.",
          robots_disallowed: "Este sitio no permite el analisis automatico (robots.txt).",
        };
        throw new Error(
          messages[data.error_reason ?? ""] ?? "No se pudo analizar la web indicada.",
        );
      }

      const newlySuggested = new Set<SuggestedField>();

      if (data.suggested_company_name || data.suggested_business_type) {
        setPayload((current) => ({
          ...current,
          ...(data.suggested_company_name ? { company_name: data.suggested_company_name } : {}),
          ...(data.suggested_business_type ? { business_type: data.suggested_business_type } : {}),
        }));
        if (data.suggested_company_name) newlySuggested.add("company_name");
        if (data.suggested_business_type) newlySuggested.add("business_type");
      }

      if (data.suggested_current_tools.length > 0) {
        setToolsText(data.suggested_current_tools.join("\n"));
        newlySuggested.add("current_tools");
      }

      setSuggestedFields(newlySuggested);
      setCandidatePainPoints(data.candidate_pain_points);
      setSelectedCandidates(new Set(data.candidate_pain_points));
      setCandidateObjective(data.candidate_objectives);
    } catch (caughtError) {
      setEnrichError(caughtError instanceof Error ? caughtError.message : "Error inesperado.");
    } finally {
      setIsEnriching(false);
    }
  }

  const selectedBusiness = useMemo(
    () => businessTypes.find((item) => item.value === payload.business_type)?.label,
    [payload.business_type],
  );

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setIsLoading(true);

    const requestPayload = {
      ...payload,
      employee_count: Number(employeeCountText),
      pain_points: splitLines(painPointsText),
      current_tools: splitLines(toolsText),
    };

    try {
      const response = await fetch(`${API_URL}/api/v1/diagnostics/proposal`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(requestPayload),
      });

      if (!response.ok) {
        throw new Error(await extractErrorMessage(response, "No se pudo generar la propuesta."));
      }

      const data = (await response.json()) as DiagnosticResponse | ProposalGenerationError;
      if (isProposalError(data)) {
        throw new Error(
          "No pudimos generar tu propuesta con IA en este momento. Intentalo de nuevo en unos minutos.",
        );
      }

      setProposal(data);
    } catch (caughtError) {
      setError(caughtError instanceof Error ? caughtError.message : "Error inesperado.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="shell">
      <section className="panel diagnostic-panel" aria-label="Diagnostico">
        <div className="panel-head">
          <div className="brand-lockup">
            <div className="mark">
              <Gauge size={18} />
            </div>
            <div>
              <div className="eyebrow">Automation Preview</div>
              <h1>Diagnostico</h1>
            </div>
          </div>
          {proposal ? (
            <div className="status-pill">
              <CheckCircle2 size={14} />
              {proposal.provider}
            </div>
          ) : null}
        </div>

        <form className="form" onSubmit={handleSubmit}>
          <div className="field enrichment-field">
            <label htmlFor="website">Web del negocio (opcional)</label>
            <div className="enrichment-row">
              <input
                id="website"
                type="url"
                placeholder="https://tuempresa.com"
                value={websiteUrl}
                onChange={(event) => setWebsiteUrl(event.target.value)}
              />
              <button
                className="ghost-button"
                type="button"
                disabled={!websiteUrl || !allowScraping || isEnriching}
                onClick={handleEnrichWebsite}
              >
                {isEnriching ? <Loader2 className="spin" size={16} /> : <Globe size={16} />}
                Analizar mi web
              </button>
            </div>
            {isEnriching ? (
              <span className="suggested-hint">
                Analizando la web, puede tardar hasta 25 segundos en sitios grandes...
              </span>
            ) : null}
            <label className="checkbox-row">
              <input
                type="checkbox"
                checked={allowScraping}
                onChange={(event) => setAllowScraping(event.target.checked)}
              />
              Autorizo analizar mi web para precargar el diagnostico
            </label>
            {enrichError ? (
              <div className="error">
                <AlertCircle size={17} />
                <span>{enrichError}</span>
              </div>
            ) : null}
          </div>

          {candidatePainPoints.length > 0 || candidateObjective ? (
            <div className="field candidates-panel">
              <div className="candidates-header">
                <span className="suggested-hint">Sugerencias detectadas en la web</span>
                <button type="button" className="ghost-button" onClick={dismissCandidates}>
                  Descartar
                </button>
              </div>

              {candidatePainPoints.length > 0 ? (
                <div className="candidates-block">
                  <label>Posibles pain points</label>
                  {candidatePainPoints.map((point) => (
                    <label key={point} className="candidate-item">
                      <input
                        type="checkbox"
                        checked={selectedCandidates.has(point)}
                        onChange={() => toggleCandidatePainPoint(point)}
                      />
                      {point}
                    </label>
                  ))}
                  <button
                    type="button"
                    className="ghost-button"
                    onClick={addSelectedCandidatePainPoints}
                  >
                    Anadir seleccionados a Pain points
                  </button>
                </div>
              ) : null}

              {candidateObjective ? (
                <div className="candidates-block">
                  <label>Objetivo sugerido</label>
                  <p className="candidate-objective-text">{candidateObjective}</p>
                  <button type="button" className="ghost-button" onClick={useCandidateObjective}>
                    Usar esta sugerencia
                  </button>
                </div>
              ) : null}
            </div>
          ) : null}

          <div className="field">
            <label htmlFor="company">Empresa</label>
            <input
              id="company"
              name="organization"
              autoComplete="organization"
              required
              className={suggestedFields.has("company_name") ? "suggested" : undefined}
              placeholder="Nombre de la empresa"
              value={payload.company_name}
              onChange={(event) => {
                clearSuggestion("company_name");
                setPayload((current) => ({ ...current, company_name: event.target.value }));
              }}
            />
            {suggestedFields.has("company_name") ? (
              <span className="suggested-hint">Sugerido, verifica o edita</span>
            ) : null}
          </div>

          <div className="two-col">
            <div className="field">
              <label htmlFor="business">Negocio</label>
              <select
                id="business"
                required
                className={suggestedFields.has("business_type") ? "suggested" : undefined}
                value={payload.business_type}
                onChange={(event) => {
                  clearSuggestion("business_type");
                  setPayload((current) => ({
                    ...current,
                    business_type: event.target.value as BusinessType,
                  }));
                }}
              >
                <option value="" disabled>
                  Tipo de negocio o sector
                </option>
                {businessTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
              {suggestedFields.has("business_type") ? (
                <span className="suggested-hint">Sugerido, verifica o edita</span>
              ) : null}
            </div>

            <div className="field">
              <label htmlFor="employees">Empleados</label>
              <input
                id="employees"
                required
                min={1}
                max={5000}
                type="number"
                placeholder="Ej. 12"
                value={employeeCountText}
                onChange={(event) => setEmployeeCountText(event.target.value)}
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="goal">Objetivo</label>
            <textarea
              id="goal"
              required
              spellCheck={false}
              className={suggestedFields.has("automation_goal") ? "suggested" : undefined}
              placeholder="Ej. Reducir tareas manuales, mejorar el seguimiento de clientes y organizar mejor la comunicacion interna."
              value={payload.automation_goal}
              onChange={(event) => {
                clearSuggestion("automation_goal");
                setPayload((current) => ({ ...current, automation_goal: event.target.value }));
              }}
            />
            {suggestedFields.has("automation_goal") ? (
              <span className="suggested-hint">Sugerido, verifica o edita</span>
            ) : null}
          </div>

          <div className="field">
            <label htmlFor="pain">Pain points</label>
            <textarea
              id="pain"
              required
              spellCheck={false}
              className={suggestedFields.has("pain_points") ? "suggested" : undefined}
              placeholder={"Un pain point por linea. Ej.\nMucho tiempo confirmando citas\nInformacion dispersa entre herramientas"}
              value={painPointsText}
              onChange={(event) => {
                clearSuggestion("pain_points");
                setPainPointsText(event.target.value);
              }}
            />
            {suggestedFields.has("pain_points") ? (
              <span className="suggested-hint">Sugerido, verifica o edita</span>
            ) : null}
          </div>

          <div className="field">
            <label htmlFor="tools">Herramientas actuales</label>
            <textarea
              id="tools"
              spellCheck={false}
              className={suggestedFields.has("current_tools") ? "suggested" : undefined}
              placeholder={"Una herramienta por linea. Ej.\nGoogle Calendar\nWhatsApp"}
              value={toolsText}
              onChange={(event) => {
                clearSuggestion("current_tools");
                setToolsText(event.target.value);
              }}
            />
            {suggestedFields.has("current_tools") ? (
              <span className="suggested-hint">Sugerido, verifica o edita</span>
            ) : null}
          </div>

          <div className="field">
            <label htmlFor="contact">Contacto</label>
            <select
              id="contact"
              value={payload.preferred_contact}
              onChange={(event) =>
                setPayload((current) => ({
                  ...current,
                  preferred_contact: event.target.value as DiagnosticPayload["preferred_contact"],
                }))
              }
            >
              <option value="email">Email</option>
              <option value="phone">Telefono</option>
              <option value="whatsapp">WhatsApp</option>
              <option value="not_specified">No especificado</option>
            </select>
          </div>

          {error ? (
            <div className="error">
              <AlertCircle size={17} />
              <span>{error}</span>
            </div>
          ) : null}

          <div className="actions">
            <button className="primary-button" type="submit" disabled={isLoading}>
              {isLoading ? <Loader2 className="spin" size={17} /> : <Send size={17} />}
              Generar propuesta
            </button>
            <button
              className="ghost-button"
              type="button"
              onClick={() => {
                setPayload(initialPayload);
                setPainPointsText(initialPayload.pain_points.join("\n"));
                setToolsText(initialPayload.current_tools.join("\n"));
                setEmployeeCountText("");
                setProposal(null);
                setError("");
                setWebsiteUrl("");
                setAllowScraping(false);
                setEnrichError("");
                setSuggestedFields(new Set());
                dismissCandidates();
              }}
            >
              <RefreshCw size={16} />
              Reset
            </button>
          </div>
        </form>
      </section>

      {proposal ? (
        <section className="proposal" aria-label="Propuesta">
          <div className="panel summary-band">
            <div className="summary-grid">
              <div className="summary-copy">
                <div className="meta-row">
                  <span className="chip">
                    <BriefcaseBusiness size={14} />
                    {selectedBusiness}
                  </span>
                  <span className="chip">
                    <ClipboardList size={14} />
                    {proposal.automations.length} automatizaciones
                  </span>
                </div>
                <h2>{proposal.company_name}</h2>
                <p>{proposal.executive_summary}</p>
                <p>{proposal.recommended_automation}</p>
              </div>

              <div className="roi">
                <div className="card-top">
                  <h3>ROI orientativo</h3>
                  <BarChart3 size={18} />
                </div>
                <p>{proposal.roi.headline}</p>
                <ul>
                  {proposal.roi.benefits.slice(0, 3).map((benefit) => (
                    <li key={benefit}>{benefit}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div className="section">
            <div className="section-title">
              <h2>Automatizaciones</h2>
              <span className="chip">
                <Sparkles size={14} />
                Quick wins primero
              </span>
            </div>
            <div className="automation-grid">
              {proposal.automations.map((automation) => (
                <article className="automation-card" key={automation.solucion_propuesta}>
                  <div className="card-top">
                    <h3>{automation.solucion_propuesta}</h3>
                    <span className="tag">{automation.tipo.replace("_", " ")}</span>
                  </div>
                  <p>{automation.problema_detectado}</p>
                  <ul>
                    <li>{automation.beneficio_operativo}</li>
                    <li>{automation.impacto_estimado}</li>
                    <li>Dificultad {automation.dificultad}</li>
                  </ul>
                </article>
              ))}
            </div>
          </div>

          <div className="section">
            <div className="section-title">
              <h2>Workflow visual</h2>
              <span className="chip">
                <Workflow size={14} />
                Flujo operativo
              </span>
            </div>
            <div className="panel flow-wrap">
              <div className="flow-line" />
              <div className="flow-grid">
                {proposal.flow.map((step, index) => (
                  <article className="flow-step" key={step.id}>
                    <div className="card-top">
                      <div className="node-icon">
                        <IconForStep name={step.suggested_icon} />
                      </div>
                      <span className="tag">{String(index + 1).padStart(2, "0")}</span>
                    </div>
                    <div>
                      <h3>{step.title}</h3>
                      <p>{step.short_description}</p>
                    </div>
                    <div className="io">
                      <div>
                        <strong>Inputs</strong>
                        <ul>
                          {step.inputs.map((input) => (
                            <li key={input}>{input}</li>
                          ))}
                        </ul>
                      </div>
                      <div>
                        <strong>Outputs</strong>
                        <ul>
                          {step.outputs.map((output) => (
                            <li key={output}>{output}</li>
                          ))}
                        </ul>
                      </div>
                    </div>
                    <p>{step.estimated_impact}</p>
                  </article>
                ))}
              </div>
            </div>
          </div>

          <div className="section">
            <div className="section-title">
              <h2>Fases</h2>
              <span className="chip">
                <ArrowRight size={14} />
                Alcance ajustable
              </span>
            </div>
            <div className="panel summary-band">
              <ol className="phase-list">
                {proposal.implementation_phases.map((phase) => (
                  <li key={phase}>{phase}</li>
                ))}
              </ol>
            </div>
          </div>

          <div className="cta">
            <h2>Siguiente paso</h2>
            <p>{proposal.contact_cta}</p>
            <p>{proposal.disclaimer}</p>
          </div>
        </section>
      ) : (
        <section className="panel empty">
          <div className="empty-inner">
            <Network size={36} />
            <h2>Propuesta pendiente</h2>
            <p>Completa el diagnostico para ver el flujo y las automatizaciones sugeridas.</p>
          </div>
        </section>
      )}
    </main>
  );
}
