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
  | "other";

type DiagnosticPayload = {
  company_name: string;
  business_type: BusinessType;
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

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://127.0.0.1:8000";

const businessTypes: Array<{ value: BusinessType; label: string }> = [
  { value: "law_firm", label: "Bufete de abogados" },
  { value: "dental_clinic", label: "Clinica dental" },
  { value: "notary", label: "Notaria" },
  { value: "gestoria", label: "Gestoria / asesoria" },
  { value: "real_estate", label: "Inmobiliaria" },
  { value: "ecommerce", label: "Ecommerce" },
  { value: "professional_services", label: "Servicios profesionales" },
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

const sampleProposal: DiagnosticResponse = {
  company_name: "Clinica Sonrisa Norte",
  business_type: "dental_clinic",
  executive_summary:
    "Clinica Sonrisa Norte puede iniciar con una automatizacion enfocada en agenda, recordatorios y seguimiento de pacientes para reducir carga administrativa.",
  recommended_automation:
    "Un flujo inicial conectaria la entrada de solicitudes, confirmacion de citas, avisos automaticos y seguimiento post-tratamiento con una medicion simple de resultados.",
  automations: [
    {
      problema_detectado: "Recepcion saturada por llamadas y confirmaciones manuales",
      solucion_propuesta: "Recordatorios automaticos de cita por email o WhatsApp",
      beneficio_operativo: "Menos llamadas repetitivas y mayor orden en recepcion",
      impacto_estimado: "Alto impacto inicial sin cambiar el sistema principal",
      dificultad: "baja",
      tipo: "quick_win",
    },
    {
      problema_detectado: "Seguimiento irregular de presupuestos",
      solucion_propuesta: "Secuencia de seguimiento para presupuestos pendientes",
      beneficio_operativo: "Mejor continuidad comercial y menos oportunidades perdidas",
      impacto_estimado: "Impacto visible en conversion y respuesta",
      dificultad: "media",
      tipo: "medio_plazo",
    },
    {
      problema_detectado: "Falta de visibilidad sobre no-shows y carga operativa",
      solucion_propuesta: "Panel operativo con citas, ausencias y tareas abiertas",
      beneficio_operativo: "Mejor toma de decisiones semanal",
      impacto_estimado: "Mejora progresiva del control interno",
      dificultad: "media",
      tipo: "medio_plazo",
    },
  ],
  flow: [
    {
      id: "contact",
      title: "Toma de contacto",
      short_description: "Recogemos contexto, herramientas actuales y prioridades.",
      step_type: "start",
      owner: "team",
      inputs: ["Diagnostico", "Canal preferido"],
      outputs: ["Mapa inicial"],
      suggested_icon: "messages-square",
      estimated_impact: "Alineacion rapida del alcance.",
    },
    {
      id: "analysis",
      title: "Analisis operativo",
      short_description: "Detectamos cuellos de botella y quick wins.",
      step_type: "process",
      owner: "automation",
      inputs: ["Pain points", "Herramientas"],
      outputs: ["Prioridades"],
      suggested_icon: "workflow",
      estimated_impact: "Foco en bajo riesgo y alto impacto.",
    },
    {
      id: "automation",
      title: "Automatizacion inicial",
      short_description: "Activamos captura, avisos y seguimiento.",
      step_type: "automation",
      owner: "system",
      inputs: ["Citas", "Solicitudes", "Eventos"],
      outputs: ["Recordatorios", "Tareas", "Registro"],
      suggested_icon: "bot",
      estimated_impact: "Reduccion de trabajo manual.",
    },
    {
      id: "validation",
      title: "Validacion",
      short_description: "Revisamos excepciones y aprobaciones del equipo.",
      step_type: "validation",
      owner: "team",
      inputs: ["Flujo piloto"],
      outputs: ["Ajustes"],
      suggested_icon: "shield-check",
      estimated_impact: "Adopcion mas sencilla.",
    },
    {
      id: "roi",
      title: "ROI y propuesta",
      short_description: "Aterrizamos fases, beneficios y siguiente paso.",
      step_type: "end",
      owner: "team",
      inputs: ["Flujo validado"],
      outputs: ["Propuesta preliminar"],
      suggested_icon: "chart-no-axes-combined",
      estimated_impact: "Decision comercial mas clara.",
    },
  ],
  roi: {
    headline: "El retorno vendria de reducir tareas manuales y mejorar tiempos de respuesta.",
    assumptions: [
      "La estimacion final requiere conocer volumen mensual de citas y canales reales.",
      "El alcance depende de integraciones disponibles y calidad de datos.",
    ],
    benefits: [
      "Menos llamadas repetitivas.",
      "Mejor seguimiento de pacientes.",
      "Mas visibilidad para recepcion y direccion.",
    ],
  },
  implementation_phases: [
    "Diagnostico y diseno del flujo prioritario.",
    "Prototipo con recordatorios, tareas y seguimiento.",
    "Validacion, ajustes y medicion de beneficios.",
  ],
  contact_cta:
    "Agenda una toma de contacto para ajustar alcance, integraciones, presupuesto y requisitos reales del negocio.",
  disclaimer:
    "Esta propuesta es preliminar y orientativa. La solucion final requiere analisis del negocio, herramientas disponibles e integraciones necesarias.",
  provider: "mock",
};

const initialPayload: DiagnosticPayload = {
  company_name: "Clinica Sonrisa Norte",
  business_type: "dental_clinic",
  employee_count: 12,
  automation_goal: "Reducir llamadas y organizar citas, recordatorios y seguimientos.",
  pain_points: [
    "Mucho tiempo confirmando citas",
    "Pacientes que no acuden",
    "Informacion dispersa entre agenda email y WhatsApp",
  ],
  current_tools: ["Google Calendar", "WhatsApp", "Excel"],
  preferred_contact: "email",
};

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
  const [proposal, setProposal] = useState<DiagnosticResponse>(sampleProposal);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

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
        const detail = await response.text();
        throw new Error(detail || "No se pudo generar la propuesta.");
      }

      const data = (await response.json()) as DiagnosticResponse;
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
          <div className="status-pill">
            <CheckCircle2 size={14} />
            {proposal.provider}
          </div>
        </div>

        <form className="form" onSubmit={handleSubmit}>
          <div className="field">
            <label htmlFor="company">Empresa</label>
            <input
              id="company"
              value={payload.company_name}
              onChange={(event) =>
                setPayload((current) => ({ ...current, company_name: event.target.value }))
              }
            />
          </div>

          <div className="two-col">
            <div className="field">
              <label htmlFor="business">Negocio</label>
              <select
                id="business"
                value={payload.business_type}
                onChange={(event) =>
                  setPayload((current) => ({
                    ...current,
                    business_type: event.target.value as BusinessType,
                  }))
                }
              >
                {businessTypes.map((type) => (
                  <option key={type.value} value={type.value}>
                    {type.label}
                  </option>
                ))}
              </select>
            </div>

            <div className="field">
              <label htmlFor="employees">Empleados</label>
              <input
                id="employees"
                min={1}
                max={5000}
                type="number"
                value={payload.employee_count}
                onChange={(event) =>
                  setPayload((current) => ({
                    ...current,
                    employee_count: Number(event.target.value),
                  }))
                }
              />
            </div>
          </div>

          <div className="field">
            <label htmlFor="goal">Objetivo</label>
            <textarea
              id="goal"
              value={payload.automation_goal}
              onChange={(event) =>
                setPayload((current) => ({ ...current, automation_goal: event.target.value }))
              }
            />
          </div>

          <div className="field">
            <label htmlFor="pain">Pain points</label>
            <textarea
              id="pain"
              value={painPointsText}
              onChange={(event) => setPainPointsText(event.target.value)}
            />
          </div>

          <div className="field">
            <label htmlFor="tools">Herramientas actuales</label>
            <textarea
              id="tools"
              value={toolsText}
              onChange={(event) => setToolsText(event.target.value)}
            />
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
                setProposal(sampleProposal);
                setError("");
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
