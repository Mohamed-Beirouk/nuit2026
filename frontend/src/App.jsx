import { useCallback, useEffect, useState } from "react";

// The dev server proxies /api. A deployed build has no proxy, so it calls the API host.
const API_BASE =
  import.meta.env.VITE_API_BASE ??
  (import.meta.env.DEV ? "" : "https://api-nuit2026.beirouk.dev");

async function readClaims() {
  const response = await fetch(`${API_BASE}/api/claims/`);
  const data = await response.json().catch(() => ({}));
  if (!response.ok || !Array.isArray(data.claims)) {
    throw new Error(data.detail || "Could not load the counter.");
  }
  return data;
}

export default function App() {
  const [name, setName] = useState("");
  const [counter, setCounter] = useState(0);
  const [claims, setClaims] = useState([]);
  const [mine, setMine] = useState(null);
  const [pending, setPending] = useState(false);
  const [error, setError] = useState("");

  const load = useCallback(async () => {
    const data = await readClaims();
    setCounter(data.counter);
    setClaims(data.claims);
  }, []);

  useEffect(() => {
    let cancelled = false;
    load().catch((err) => {
      if (!cancelled) setError(err.message);
    });
    const timer = setInterval(() => {
      load().catch(() => {});
    }, 2000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [load]);

  async function onSubmit(event) {
    event.preventDefault();
    const trimmed = name.trim();
    if (!trimmed || pending) return;

    setPending(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/api/claims/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name: trimmed }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || "Could not take a number.");
      }
      setMine(data);
      setName("");
      await load();
    } catch (err) {
      setError(err.message);
    } finally {
      setPending(false);
    }
  }

  const taken = Array.isArray(claims) ? claims : [];

  return (
    <main>
      <p className="eyebrow">Shared counter</p>
      <h1>Take the next number</h1>
      <p className="lede">
        The counter is at <strong>{counter}</strong>. The next click gets{" "}
        <strong>{counter + 1}</strong>, saved with your name.
      </p>

      <form onSubmit={onSubmit}>
        <label htmlFor="name">Your name</label>
        <input
          id="name"
          name="name"
          value={name}
          maxLength={80}
          autoComplete="name"
          placeholder="beirouk"
          onChange={(event) => setName(event.target.value)}
        />
        <button type="submit" disabled={pending || name.trim() === ""}>
          {pending ? "Saving…" : "Take the next number"}
        </button>
      </form>

      {error ? (
        <p className="error" role="alert">
          {error}
        </p>
      ) : null}

      {mine ? (
        <p className="ticket" role="status">
          <span>{mine.name}</span>
          <strong>{mine.number}</strong>
        </p>
      ) : null}

      <section className="ledger" aria-label="Numbers already taken">
        <h2>Who has a number</h2>
        {taken.length === 0 ? (
          <p className="empty">Nobody yet.</p>
        ) : (
          <ol>
            {taken.map((claim) => (
              <li key={claim.id}>
                <span className="num">{claim.number}</span>
                <span>{claim.name}</span>
              </li>
            ))}
          </ol>
        )}
      </section>
    </main>
  );
}
