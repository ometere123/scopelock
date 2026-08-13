import Link from "next/link";

export default function Home() {
  return (
    <main>
      <section className="hero" aria-labelledby="title">
        <p className="eyebrow">PUBLIC SECURITY DISCLOSURE / GENLAYER CONSENSUS</p>
        <h1 id="title">Public findings.<br />Bound scope.<br /><em>Consensus settlement.</em></h1>
        <aside className="brief">
          <span>01 / WHAT GETS LOCKED</span>
          <p>Sponsors lock GEN against a pinned public target. Researchers bond public disclosures. ScopeLock settles only after independent evidence review.</p>
          <Link href="/programs">Browse active scopes →</Link>
        </aside>
      </section>

      <section className="ledger-section">
        <div className="section-heading"><span>02 / PROGRAM INDEX</span><p>On-chain program data appears here. Connect to load the active network.</p></div>
        <div className="empty-ledger">
          <strong>NO PROGRAMS LOADED</strong>
          <p>ScopeLock never fabricates sponsors, balances, disclosures, or consensus results. Configure a deployed contract to read the public program index.</p>
          <Link href="/programs/new">Create a program →</Link>
        </div>
      </section>

      <section className="precedent">
        <div><p className="eyebrow">03 / PRECEDENT DISCOVERY</p><h2>Similarity is a search signal.<br />It is not a verdict.</h2></div>
        <div className="comparison">
          <div><span>CURRENT DISCLOSURE</span><strong>Awaiting report</strong><p>Target, affected component, and researcher-supplied search synopsis are embedded deterministically.</p></div>
          <div><span>POSSIBLE PRECEDENT</span><strong>Chain data required</strong><p>Only settled reports in the same program are candidates. Distance can never pay, slash, or reject.</p></div>
        </div>
      </section>

      <section className="rail-section">
        <div><p className="eyebrow">04 / SCOPE RAIL</p><h2>A disclosure dossier is a record, not a dashboard.</h2></div>
        <ol className="rail">
          <li><time>01</time><b>SUBMISSION BOUND</b><small>Researcher bond and immutable program scope recorded on-chain.</small></li>
          <li><time>02</time><b>PRECEDENT SCAN</b><small>Deterministic scoped candidate selection; never a duplicate decision.</small></li>
          <li><time>03</time><b>CONSENSUS</b><small>Validators independently inspect public evidence and target context.</small></li>
          <li><time>04</time><b>SETTLEMENT</b><small>Contract maps the agreed verdict to the program’s fixed GEN matrix.</small></li>
        </ol>
      </section>

      <footer>ScopeLock is a public-evidence MVP. No hidden backend decides eligibility or moves GEN. <span>POWERED BY GENLAYER</span></footer>
    </main>
  );
}
