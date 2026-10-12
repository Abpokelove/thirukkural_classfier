import { useEffect, useMemo, useState, type ChangeEvent } from 'react'
import Papa from 'papaparse'

type Candidate = {
  kural_number: number
  chapter: string | number
  text: string
  score: number
  matching_reason: string
}

type VerificationResult = {
  text_status: string
  human_label: string
  technical_label: string
  presentation_status: string
  attribution_status: string
  normalization: { L0_match: boolean; L1_match: boolean; L2_match: boolean; L0: string; L1: string; L2: string }
  signals: { character_similarity: number; edit_distance: number; lexical_similarity: number; semantic_similarity: number | null }
  possible_originals: Candidate[]
  evidence: { matched_kural: number | null; coverage: number; contiguous: boolean; candidate_rank: number | null; claim_supported: boolean }
  why: string[]
  claimed_kural_number?: number | string | null
  best_candidate?: { kural_number: number; chapter: string | number; chapter_number?: string | number; text: string; score: number } | null
  matched_text?: string | null
  chapter_number?: string | number | null
  line1?: string | null
  line2?: string | null
}

type CorpusItem = {
  kural_number: number
  chapter: string | number
  chapter_number: string | number
  line1: string
  line2: string
  text: string
}

type BatchResult = {
  response_id?: string | null
  model?: string | null
  prompt?: string | null
  quotation: string
  claimed_kural_number?: number | string | null
  result: VerificationResult
}

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(/\/+$/, '')
const defaultQuote = 'அகர முதல எழுத்தெல்லாம் ஆதி பகவன் முதற்றே உலகு.'

function App() {
  const [activeTab, setActiveTab] = useState<'verify' | 'batch' | 'research' | 'explore' | 'validation'>('verify')
  const [quote, setQuote] = useState(defaultQuote)
  const [claimedKuralNumber, setClaimedKuralNumber] = useState('')
  const [result, setResult] = useState<VerificationResult | null>(null)
  const [validation, setValidation] = useState<any>(null)
  const [stats, setStats] = useState({ records: 0, chapters: 0 })
  const [loading, setLoading] = useState(false)
  const [batchRows, setBatchRows] = useState<BatchResult[]>([])
  const [batchError, setBatchError] = useState('')
  const [batchModelFilter, setBatchModelFilter] = useState('')
  const [batchStatusFilter, setBatchStatusFilter] = useState('')
  const [batchAttributionFilter, setBatchAttributionFilter] = useState('')
  const [batchPromptFilter, setBatchPromptFilter] = useState('')
  const [corpusItems, setCorpusItems] = useState<CorpusItem[]>([])
  const [corpusQuery, setCorpusQuery] = useState('')
  const [corpusChapter, setCorpusChapter] = useState('')
  const [corpusPage, setCorpusPage] = useState(0)
  const [corpusTotal, setCorpusTotal] = useState(0)
  const [corpusLoading, setCorpusLoading] = useState(false)
  const [corpusError, setCorpusError] = useState('')

  useEffect(() => {
    const loadMeta = async () => {
      try {
        const [statsRes, validationRes] = await Promise.all([
          fetch(`${API_BASE_URL}/api/corpus/stats`),
          fetch(`${API_BASE_URL}/api/validation`),
        ])
        const nextStats = await statsRes.json()
        const nextValidation = await validationRes.json()
        setStats(nextValidation.valid ? nextStats : { records: 0, chapters: 0 })
        setValidation(nextValidation)
      } catch {
        // Ignore metadata fetch failures in the initial UI render.
      }
    }
    void loadMeta()
  }, [])

  useEffect(() => {
    if (activeTab !== 'explore') return
    let current = true
    const loadPage = async () => {
      setCorpusLoading(true)
      setCorpusError('')
      const params = new URLSearchParams({ offset: String(corpusPage * 20), limit: '20' })
      if (corpusQuery.trim()) params.set('query', corpusQuery.trim())
      if (corpusChapter) params.set('chapter', corpusChapter)
      try {
        const response = await fetch(`${API_BASE_URL}/api/corpus/browse?${params.toString()}`)
        if (!response.ok) throw new Error(`Corpus request failed (${response.status})`)
        const payload = await response.json()
        if (current) {
          setCorpusItems(payload.items)
          setCorpusTotal(payload.total)
        }
      } catch (error) {
        if (current) setCorpusError(error instanceof Error ? error.message : 'Unable to load corpus records.')
      } finally {
        if (current) setCorpusLoading(false)
      }
    }
    void loadPage()
    return () => { current = false }
  }, [activeTab, corpusPage, corpusQuery, corpusChapter])

  const statCards = useMemo(
    () => [
      { label: 'Reference Corpus', value: stats.records ? `${stats.records} Kurals` : 'Unavailable' },
      { label: 'Chapters', value: stats.chapters ? `${stats.chapters}` : 'Unavailable' },
      { label: 'Verification Method', value: 'Evidence-Grounded' },
      { label: 'Source', value: 'Project Madurai' },
    ],
    [stats],
  )

  async function handleVerify() {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/api/verify`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          quotation: quote,
          claimed_kural_number: claimedKuralNumber ? Number(claimedKuralNumber) : null,
        }),
      })
      const payload = (await response.json()) as VerificationResult
      setResult(payload)
    } catch (error) {
      setResult({
        text_status: 'AMBIGUOUS',
        human_label: 'Needs Review',
        technical_label: 'AMBIGUOUS',
        presentation_status: 'NOT_CLEAR',
        attribution_status: 'NOT_PROVIDED',
        normalization: { L0_match: false, L1_match: false, L2_match: false, L0: '', L1: '', L2: '' },
        signals: { character_similarity: 0, edit_distance: 0, lexical_similarity: 0, semantic_similarity: null },
        possible_originals: [],
        evidence: { matched_kural: null, coverage: 0, contiguous: false, candidate_rank: null, claim_supported: false },
        why: [`Unable to connect to the verification backend: ${error instanceof Error ? error.message : 'unknown error'}`],
      })
    } finally {
      setLoading(false)
    }
  }

  function handleBatchFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setBatchError('')
    Papa.parse<Record<string, string>>(file, {
      header: true,
      skipEmptyLines: true,
      complete: async ({ data, meta, errors }) => {
        if (errors.length) {
          setBatchError(errors[0].message)
          return
        }
        if (!meta.fields?.includes('quotation')) {
          setBatchError('The CSV must include a quotation column.')
          return
        }
        const items = data.filter((row) => row.quotation?.trim()).map((row) => ({
          response_id: row.response_id || null,
          model: row.model || null,
          prompt: row.prompt || null,
          quotation: row.quotation,
          claimed_kural_number: row.claimed_kural_number?.trim() || null,
        }))
        if (!items.length) {
          setBatchError('No non-empty quotations were found in the CSV.')
          return
        }
        setLoading(true)
        try {
          const response = await fetch(`${API_BASE_URL}/api/batch/verify`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(items),
          })
          if (!response.ok) throw new Error(`Batch verification failed (${response.status})`)
          setBatchRows(await response.json())
        } catch (error) {
          setBatchError(error instanceof Error ? error.message : 'Unable to verify this batch.')
        } finally {
          setLoading(false)
        }
      },
    })
  }

  function exportBatchResults() {
    const csv = Papa.unparse(batchRows.map((row) => ({
      response_id: row.response_id ?? '',
      model: row.model ?? '',
      prompt: row.prompt ?? '',
      quotation: row.quotation,
      predicted_status: row.result.text_status,
      matched_kural: row.result.evidence.matched_kural ?? '',
      attribution: row.result.attribution_status,
      presentation: row.result.presentation_status,
      explanation: row.result.why.join(' '),
    })))
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = 'thirukkural-verification-results.csv'
    link.click()
    URL.revokeObjectURL(url)
  }

  async function copyText(text: string) {
    await navigator.clipboard.writeText(text)
  }

  const filteredBatchRows = batchRows.filter((row) =>
    (!batchModelFilter || row.model === batchModelFilter)
    && (!batchStatusFilter || row.result.text_status === batchStatusFilter)
    && (!batchAttributionFilter || row.result.attribution_status === batchAttributionFilter)
    && (!batchPromptFilter || (row.prompt ?? '').toLowerCase().includes(batchPromptFilter.toLowerCase())),
  )
  const modelOptions = [...new Set(batchRows.map((row) => row.model).filter((value): value is string => Boolean(value)))]
  const experimentMetrics = batchRows.reduce<Record<string, number>>((counts, row) => {
    const status = row.result.text_status
    counts[status] = (counts[status] ?? 0) + 1
    counts.total = (counts.total ?? 0) + 1
    return counts
  }, {})

  return (
    <div className="lab-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">THIRUKKURAL</p>
          <h1>RELIABILITY LAB</h1>
        </div>
        <p className="subtitle">Evidence-Grounded Verification of LLM-Generated Classical Tamil Quotations</p>
      </header>

      <nav className="tab-bar" aria-label="Main sections">
        <button type="button" className={activeTab === 'verify' ? 'tab active' : 'tab'} onClick={() => setActiveTab('verify')}>
          Verification Workspace
        </button>
        <button type="button" className={activeTab === 'batch' ? 'tab active' : 'tab'} onClick={() => setActiveTab('batch')}>
          Batch Experiment
        </button>
        <button type="button" className={activeTab === 'research' ? 'tab active' : 'tab'} onClick={() => setActiveTab('research')}>
          Research Dashboard
        </button>
        <button type="button" className={activeTab === 'explore' ? 'tab active' : 'tab'} onClick={() => setActiveTab('explore')}>
          Corpus Explorer
        </button>
        <button type="button" className={activeTab === 'validation' ? 'tab active' : 'tab'} onClick={() => setActiveTab('validation')}>
          Corpus Validation
        </button>
      </nav>

      <section className="stats-grid">
        {statCards.map((card) => (
          <article key={card.label} className="stat-card">
            <span>{card.label}</span>
            <strong>{card.value}</strong>
          </article>
        ))}
      </section>

      {activeTab === 'verify' && (
        <main className="workspace-grid">
          <section className="panel input-panel">
            <div className="panel-heading">
              <h2>Quotation to Verify</h2>
            </div>
            <textarea
              aria-label="Quotation to verify"
              value={quote}
              onChange={(event) => { setQuote(event.target.value); setResult(null) }}
              placeholder="Paste a Tamil quotation here..."
            />

            <label className="field-label" htmlFor="claimed-kural">Claimed Kural Number</label>
            <input
              id="claimed-kural"
              value={claimedKuralNumber}
              onChange={(event) => { setClaimedKuralNumber(event.target.value); setResult(null) }}
              placeholder="Optional"
              inputMode="numeric"
            />

            <div className="actions">
              <button type="button" onClick={handleVerify} disabled={loading}>{loading ? 'Verifying…' : 'Verify Quotation'}</button>
              <button type="button" className="secondary" onClick={() => { setQuote(defaultQuote); setClaimedKuralNumber(''); setResult(null) }}>
                Clear
              </button>
            </div>
          </section>

          <section className="panel result-panel">
            <div className="panel-heading">
              <h2>Results</h2>
            </div>
            {result ? (
              <>
                <div className="badge-row">
                  <span className="result-badge">{result.human_label}</span>
                  <small>{result.technical_label}</small>
                </div>
                <p className="result-summary">{result.why?.[0] ?? 'No summary is available yet.'}</p>

                {result.claimed_kural_number !== null && result.claimed_kural_number !== undefined && (
                  <div className={`attribution-result ${result.attribution_status.toLowerCase()}`} role="status">
                    <span className="mini-label">Separate attribution check</span>
                    <strong>
                      {result.attribution_status === 'INCORRECT' ? 'Wrong Kural Number' :
                        result.attribution_status === 'CORRECT' ? 'Kural Number Correct' : 'Kural Number Unsupported'}
                    </strong>
                    <p>
                      {result.attribution_status === 'INCORRECT'
                        ? `This is an authentic quotation from Kural ${result.evidence.matched_kural}, not Kural ${result.claimed_kural_number}.`
                        : result.attribution_status === 'CORRECT'
                          ? `The quotation matches the supplied Kural ${result.claimed_kural_number}.`
                          : `The supplied number ${result.claimed_kural_number} is outside the supported Kural range (1–1330).`}
                    </p>
                  </div>
                )}

                <div className="comparison-grid">
                  <div className="quote-box">
                    <div className="mini-label">Your Quotation</div>
                    <p>{quote || '—'}</p>
                  </div>
                  <div className="quote-box reference">
                    <div className="mini-label">Closest Reference Kural</div>
                    <p>{result.best_candidate?.text ?? result.matched_text ?? 'No matching reference found.'}</p>
                  </div>
                </div>

                <div className="evidence-strip">
                  <span>Evidence Used</span>
                  {[
                    { label: 'Exact Text Match', available: result.normalization.L0_match || result.normalization.L1_match || result.normalization.L2_match },
                    { label: 'Character Match', available: result.signals.character_similarity > 0.75 },
                    { label: 'Lexical Match', available: result.signals.lexical_similarity > 0.5 },
                    { label: 'Semantic Match', available: result.signals.semantic_similarity !== null && result.signals.semantic_similarity > 0.5 },
                    { label: 'Attribution Check', available: result.attribution_status !== 'NOT_PROVIDED' },
                  ].map(({ label, available }) => (
                    <div key={label} className={available ? 'evidence-pill ok' : 'evidence-pill'}>
                      {label} <strong>{available ? 'Available' : 'Not available'}</strong>
                    </div>
                  ))}
                </div>

                <details className="details-box" open>
                  <summary>Possible Original Kurals</summary>
                  <div className="candidate-list">
                    {result.possible_originals.length > 0 ? (
                      result.possible_originals.map((candidate) => (
                        <article key={`${candidate.kural_number}-${candidate.chapter}`} className="candidate-card">
                          <div className="candidate-header">
                            <strong>Kural {candidate.kural_number}</strong>
                            <span>Chapter: {candidate.chapter}</span>
                          </div>
                          <p>{candidate.text}</p>
                          <div className="candidate-meta">
                            <span>Similarity: {(candidate.score * 100).toFixed(0)}%</span>
                            <span>{candidate.matching_reason}</span>
                          </div>
                        </article>
                      ))
                    ) : (
                      <p className="empty-state">No canonical evidence was found for this quotation.</p>
                    )}
                  </div>
                </details>

                <details className="details-box">
                  <summary>Technical Details</summary>
                  <div className="tech-grid">
                    <div><b>L0 result:</b> {result.normalization.L0_match ? 'Exact' : 'No match'}</div>
                    <div><b>L1 result:</b> {result.normalization.L1_match ? 'Formatting-normalized match' : 'No match'}</div>
                    <div><b>L2 result:</b> {result.normalization.L2_match ? 'Word-joined match' : 'No match'}</div>
                    <div><b>Edit distance:</b> {result.signals.edit_distance}</div>
                    <div><b>Character similarity:</b> {result.signals.character_similarity.toFixed(4)}</div>
                    <div><b>Lexical similarity:</b> {result.signals.lexical_similarity.toFixed(4)}</div>
                    <div><b>Semantic similarity:</b> {result.signals.semantic_similarity === null ? 'Unavailable' : result.signals.semantic_similarity.toFixed(4)}</div>
                    <div><b>Coverage:</b> {result.evidence.coverage.toFixed(2)}</div>
                    <div><b>Contiguity:</b> {result.evidence.contiguous ? 'Yes' : 'No'}</div>
                    <div><b>Claimed number:</b> {result.claimed_kural_number ?? 'Not provided'}</div>
                    <div><b>Matched number:</b> {result.evidence.matched_kural ?? 'None'}</div>
                  </div>
                </details>

                <details className="details-box">
                  <summary>How the System Decided</summary>
                  <ol className="reason-list">
                    {result.why.map((step, index) => (
                      <li key={step}>{index + 1}. {step}</li>
                    ))}
                  </ol>
                </details>
              </>
            ) : (
              <p className="empty-state">Submit a quotation to inspect the evidence trail.</p>
            )}
          </section>
        </main>
      )}

      {activeTab === 'batch' && (
        <section className="panel research-panel">
          <div className="panel-heading panel-heading-row">
            <div>
              <h2>Batch Experiment</h2>
              <p className="section-note">Import response records to verify quotations against the local corpus.</p>
            </div>
            {batchRows.length > 0 && <button type="button" className="secondary" onClick={exportBatchResults}>Download Results CSV</button>}
          </div>
          <div className="batch-import">
            <label className="field-label" htmlFor="batch-file">Experiment CSV</label>
            <input id="batch-file" type="file" accept=".csv,text/csv" onChange={handleBatchFile} disabled={loading} />
            <p className="section-note">Required: quotation. Optional: response_id, model, prompt, claimed_kural_number.</p>
            {loading && <p role="status" className="section-note">Verifying batch against the reference corpus…</p>}
            {batchError && <p role="alert" className="error-message">{batchError}</p>}
          </div>
          {batchRows.length > 0 && (
            <>
              <div className="filter-row">
                <label>Model<select value={batchModelFilter} onChange={(event) => setBatchModelFilter(event.target.value)}><option value="">All models</option>{modelOptions.map((model) => <option key={model}>{model}</option>)}</select></label>
                <label>Status<select value={batchStatusFilter} onChange={(event) => setBatchStatusFilter(event.target.value)}><option value="">All statuses</option>{[...new Set(batchRows.map((row) => row.result.text_status))].map((status) => <option key={status}>{status}</option>)}</select></label>
                <label>Attribution<select value={batchAttributionFilter} onChange={(event) => setBatchAttributionFilter(event.target.value)}><option value="">All attributions</option>{[...new Set(batchRows.map((row) => row.result.attribution_status))].map((status) => <option key={status}>{status}</option>)}</select></label>
                <label>Prompt contains<input value={batchPromptFilter} onChange={(event) => setBatchPromptFilter(event.target.value)} placeholder="Filter prompts" /></label>
              </div>
              <div className="table-wrap">
                <table>
                  <thead><tr><th>ID</th><th>Model</th><th>Quotation</th><th>Predicted Status</th><th>Matched Kural</th><th>Attribution</th></tr></thead>
                  <tbody>{filteredBatchRows.map((row, index) => (
                    <tr key={`${row.response_id ?? 'response'}-${index}`}>
                      <td>{row.response_id || '—'}</td><td>{row.model || '—'}</td><td lang="ta">{row.quotation}</td>
                      <td>{row.result.text_status}</td><td>{row.result.evidence.matched_kural ?? '—'}</td><td>{row.result.attribution_status}</td>
                    </tr>
                  ))}</tbody>
                </table>
              </div>
              <p className="section-note">Showing {filteredBatchRows.length} of {batchRows.length} verified responses. Results are retained in this browser session only.</p>
            </>
          )}
        </section>
      )}

      {activeTab === 'research' && (
        <section className="panel research-panel">
          <div className="panel-heading">
            <h2>Research Dashboard</h2>
            <p className="section-note">Metrics are calculated only from batches imported during this session.</p>
          </div>
          {batchRows.length === 0 ? (
            <div className="research-empty">
              <h3>No experiment data has been collected yet.</h3>
              <p>Import a CSV in Batch Experiment to calculate response, status, model, and prompt summaries. Corpus facts are not experiment results.</p>
              <button type="button" onClick={() => setActiveTab('batch')}>Open Batch Experiment</button>
            </div>
          ) : (
            <>
              <div className="metrics-grid">
                {[['Total responses', experimentMetrics.total ?? 0], ['Authentic', (experimentMetrics.AUTHENTIC_EXACT ?? 0) + (experimentMetrics.AUTHENTIC_FORMAT ?? 0) + (experimentMetrics.AUTHENTIC_JOINING ?? 0) + (experimentMetrics.AUTHENTIC_PARTIAL ?? 0)], ['Modified', (experimentMetrics.MODIFIED ?? 0) + (experimentMetrics.MODIFIED_MINIMAL ?? 0)], ['Blended', experimentMetrics.BLENDED ?? 0], ['Paraphrased', experimentMetrics.PARAPHRASED ?? 0], ['Fabricated', experimentMetrics.FABRICATED ?? 0], ['Needs review', experimentMetrics.AMBIGUOUS ?? 0]].map(([label, value]) => (
                  <div className="metric-cell" key={label}><span>{label}</span><strong>{value}</strong></div>
                ))}
              </div>
              <h3>Model comparison</h3>
              <div className="table-wrap"><table><thead><tr><th>Model</th><th>Total</th><th>Authenticity errors</th><th>Fabrications</th><th>Misattributions</th></tr></thead>
                <tbody>{modelOptions.map((model) => {
                  const rows = batchRows.filter((row) => row.model === model)
                  return <tr key={model}><td>{model}</td><td>{rows.length}</td><td>{rows.filter((row) => !row.result.text_status.startsWith('AUTHENTIC_')).length}</td><td>{rows.filter((row) => row.result.text_status === 'FABRICATED').length}</td><td>{rows.filter((row) => row.result.attribution_status === 'INCORRECT').length}</td></tr>
                })}</tbody>
              </table></div>
              <h3>Prompt comparison</h3>
              <div className="table-wrap"><table><thead><tr><th>Prompt</th><th>Responses</th><th>Non-authentic rate</th></tr></thead>
                <tbody>{[...new Set(batchRows.map((row) => row.prompt).filter((prompt): prompt is string => Boolean(prompt)))].map((prompt) => {
                  const rows = batchRows.filter((row) => row.prompt === prompt)
                  const errors = rows.filter((row) => !row.result.text_status.startsWith('AUTHENTIC_')).length
                  return <tr key={prompt}><td>{prompt}</td><td>{rows.length}</td><td>{((errors / rows.length) * 100).toFixed(1)}%</td></tr>
                })}</tbody>
              </table></div>
            </>
          )}
        </section>
      )}

      {activeTab === 'explore' && (
        <section className="panel research-panel">
          <div className="panel-heading">
            <h2>Corpus Explorer</h2>
            <p className="section-note">Source: Project Madurai. Search by Tamil text, Kural number, or chapter number.</p>
          </div>
          <div className="explorer-controls">
            <label>Search corpus<input value={corpusQuery} onChange={(event) => { setCorpusQuery(event.target.value); setCorpusPage(0) }} placeholder="Tamil text or Kural number" /></label>
            <label>Chapter<select value={corpusChapter} onChange={(event) => { setCorpusChapter(event.target.value); setCorpusPage(0) }}><option value="">All chapters</option>{Array.from({ length: 133 }, (_, index) => String(index + 1)).map((chapter) => <option key={chapter} value={chapter}>Chapter {chapter}</option>)}</select></label>
          </div>
          {corpusError && <p role="alert" className="error-message">{corpusError}</p>}
          {corpusLoading ? <p role="status" className="empty-state">Loading corpus records…</p> : corpusItems.length === 0 ? <p className="empty-state">No Kurals match this search.</p> : (
            <div className="corpus-list">{corpusItems.map((item) => (
              <article className="corpus-row" key={item.kural_number}>
                <div className="candidate-header"><strong>Kural {item.kural_number}</strong><span>Chapter {item.chapter_number}</span></div>
                <p lang="ta">{item.line1}<br />{item.line2}</p>
                <button type="button" className="secondary compact-button" onClick={() => void copyText(item.text)}>Copy text</button>
              </article>
            ))}</div>
          )}
          <div className="pagination-row"><span>{corpusTotal} Kurals</span><button type="button" className="secondary" onClick={() => setCorpusPage((page) => Math.max(0, page - 1))} disabled={corpusPage === 0}>Previous</button><span>Page {corpusTotal === 0 ? 0 : corpusPage + 1} of {Math.max(1, Math.ceil(corpusTotal / 20))}</span><button type="button" className="secondary" onClick={() => setCorpusPage((page) => page + 1)} disabled={(corpusPage + 1) * 20 >= corpusTotal}>Next</button></div>
        </section>
      )}

      {activeTab === 'validation' && (
        <section className="panel validation-panel">
          <div className="panel-heading">
            <h2>Corpus Validation</h2>
          </div>
          {validation ? (
            <div className="validation-grid">
              {[
                { label: '1330 Kurals detected', ok: Number(validation.record_count || 0) >= 1330 },
                { label: 'Kural numbers 1–1330', ok: validation.valid },
                { label: '133 chapters', ok: validation.valid },
                { label: '10 Kurals per chapter', ok: validation.valid },
                { label: 'UTF-8 valid', ok: validation.valid },
                { label: 'Unicode normalization checked', ok: validation.valid },
                { label: 'Duplicate check passed', ok: validation.valid },
                { label: 'Missing records: 0', ok: (validation.missing_records || []).length === 0 },
              ].map((item) => (
                <div key={item.label} className={item.ok ? 'validation-pill ok' : 'validation-pill error'}>
                  {item.ok ? '✓' : '⚠'} {item.label}
                </div>
              ))}
            </div>
          ) : (
            <p className="empty-state">Validation data is not available yet.</p>
          )}
        </section>
      )}
    </div>
  )
}

export default App
