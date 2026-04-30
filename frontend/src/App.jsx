import { useEffect, useMemo, useState } from "react";

import {
  compareItem,
  createWatchlistItem,
  deleteWatchlistItem,
  listWatchlist,
  searchItems,
  updateWatchlistItem,
} from "./api.js";

const EMPTY_WATCH_FORM = {
  target_price: "",
  notes: "",
};

const THEMES = [
  { id: "light", label: "Light" },
  { id: "dark", label: "Dark" },
  { id: "capsule", label: "Capsule" },
];

function formatIsk(value) {
  if (value === null || value === undefined || Number.isNaN(Number(value))) {
    return "No orders";
  }

  return new Intl.NumberFormat("en-US", {
    maximumFractionDigits: 2,
  }).format(Number(value));
}

function App() {
  const [theme, setTheme] = useState(() => localStorage.getItem("eve-ui-theme") ?? "dark");
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [selectedItem, setSelectedItem] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [watchlist, setWatchlist] = useState([]);
  const [watchForm, setWatchForm] = useState(EMPTY_WATCH_FORM);
  const [editingId, setEditingId] = useState(null);
  const [status, setStatus] = useState("");
  const [error, setError] = useState("");
  const [isSearching, setIsSearching] = useState(false);
  const [isComparing, setIsComparing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [searchSort, setSearchSort] = useState("name");
  const [marketOnly, setMarketOnly] = useState(true);
  const [watchFilter, setWatchFilter] = useState("");
  const [watchSort, setWatchSort] = useState("name");

  const selectedWatchItem = useMemo(
    () => watchlist.find((item) => item.id === editingId),
    [editingId, watchlist],
  );

  const bestMarket = useMemo(() => {
    if (!comparison) {
      return null;
    }

    const candidates = [
      { hub: "Jita", sell: comparison.jita.sell },
      { hub: "Amarr", sell: comparison.amarr.sell },
      { hub: "CJ", sell: comparison.cj.sell },
    ].filter((item) => item.sell !== null && item.sell !== undefined);

    return candidates.sort((first, second) => Number(first.sell) - Number(second.sell))[0] ?? null;
  }, [comparison]);

  const visibleWatchlist = useMemo(() => {
    const normalizedFilter = watchFilter.trim().toLowerCase();
    const filteredItems = watchlist.filter((item) => {
      if (!normalizedFilter) {
        return true;
      }

      return (
        item.item_name.toLowerCase().includes(normalizedFilter) ||
        (item.notes ?? "").toLowerCase().includes(normalizedFilter)
      );
    });

    return [...filteredItems].sort((first, second) => {
      if (watchSort === "target_desc") {
        return Number(second.target_price ?? -1) - Number(first.target_price ?? -1);
      }

      if (watchSort === "target_asc") {
        return (
          Number(first.target_price ?? Number.MAX_VALUE) -
          Number(second.target_price ?? Number.MAX_VALUE)
        );
      }

      if (watchSort === "newest") {
        return new Date(second.created_at).getTime() - new Date(first.created_at).getTime();
      }

      return first.item_name.localeCompare(second.item_name);
    });
  }, [watchFilter, watchSort, watchlist]);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("eve-ui-theme", theme);
  }, [theme]);

  useEffect(() => {
    refreshWatchlist();
  }, []);

  useEffect(() => {
    const trimmed = query.trim();
    setError("");

    if (trimmed.length < 2) {
      setResults([]);
      return;
    }

    const timeoutId = window.setTimeout(async () => {
      setIsSearching(true);
      try {
        const matches = await searchItems(trimmed, {
          sort: searchSort,
          marketOnly,
        });
        setResults(matches);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsSearching(false);
      }
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [marketOnly, query, searchSort]);

  async function refreshWatchlist() {
    try {
      const items = await listWatchlist();
      setWatchlist(items);
    } catch (err) {
      setError(err.message);
    }
  }

  function selectItem(item) {
    setSelectedItem(item);
    setQuery(item.name);
    setResults([]);
    setComparison(null);
    setStatus("");
    setError("");
  }

  function handleQueryChange(event) {
    setQuery(event.target.value);
    setSelectedItem(null);
    setComparison(null);
    setStatus("");
  }

  async function handleCompare() {
    if (!selectedItem) {
      setError("Select an item before comparing markets.");
      return;
    }

    setIsComparing(true);
    setError("");
    setStatus("");
    try {
      const data = await compareItem(selectedItem.type_id);
      setComparison(data);
      setStatus(`Compared ${selectedItem.name}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsComparing(false);
    }
  }

  async function handleWatchSubmit(event) {
    event.preventDefault();

    const activeItem = selectedWatchItem ?? selectedItem;
    if (!activeItem) {
      setError("Select an item before saving to the watchlist.");
      return;
    }

    const payload = {
      item_type_id: activeItem.item_type_id ?? activeItem.type_id,
      item_name: activeItem.item_name ?? activeItem.name,
      target_price: watchForm.target_price === "" ? null : Number(watchForm.target_price),
      notes: watchForm.notes === "" ? null : watchForm.notes,
    };

    setIsSaving(true);
    setError("");
    setStatus("");
    try {
      if (editingId) {
        await updateWatchlistItem(editingId, payload);
        setStatus("Watchlist item updated");
      } else {
        await createWatchlistItem(payload);
        setStatus("Watchlist item added");
      }

      setWatchForm(EMPTY_WATCH_FORM);
      setEditingId(null);
      await refreshWatchlist();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSaving(false);
    }
  }

  function beginEdit(item) {
    setEditingId(item.id);
    setWatchForm({
      target_price: item.target_price ?? "",
      notes: item.notes ?? "",
    });
    setSelectedItem({
      type_id: item.item_type_id,
      name: item.item_name,
    });
    setQuery(item.item_name);
    setStatus("");
    setError("");
  }

  async function removeWatchItem(id) {
    setError("");
    setStatus("");
    try {
      await deleteWatchlistItem(id);
      if (editingId === id) {
        setEditingId(null);
        setWatchForm(EMPTY_WATCH_FORM);
      }
      setStatus("Watchlist item removed");
      await refreshWatchlist();
    } catch (err) {
      setError(err.message);
    }
  }

  function cancelEdit() {
    setEditingId(null);
    setWatchForm(EMPTY_WATCH_FORM);
  }

  return (
    <main className="app-shell">
      <header className="topbar">
        <div className="brand-block">
          <p className="eyebrow">eve-price-compare</p>
          <h1>Market Desk</h1>
          <p className="lede">Search, compare, and track New Eden prices from one console.</p>
        </div>
        <div className="topbar-actions">
          <div className="theme-switcher" aria-label="Theme">
            {THEMES.map((item) => (
              <button
                className={theme === item.id ? "active" : ""}
                key={item.id}
                type="button"
                onClick={() => setTheme(item.id)}
              >
                {item.label}
              </button>
            ))}
          </div>
          <div className="signal-card" aria-label="Session summary">
            <span>Watchlist</span>
            <strong>{watchlist.length}</strong>
          </div>
        </div>
      </header>

      <section className="status-strip" aria-label="Market summary">
        <div>
          <span>Selected</span>
          <strong>{selectedItem?.name ?? "None"}</strong>
        </div>
        <div>
          <span>Best sell</span>
          <strong>{bestMarket ? `${bestMarket.hub} ${formatIsk(bestMarket.sell)}` : "Awaiting compare"}</strong>
        </div>
        <div>
          <span>Search matches</span>
          <strong>{results.length}</strong>
        </div>
      </section>

      <section className="workspace">
        <div className="left-pane">
          <section className="panel search-panel" aria-labelledby="search-heading">
            <div className="panel-header">
              <div>
                <h2 id="search-heading">Item Search</h2>
                <p>{selectedItem ? selectedItem.name : "Search marketable types"}</p>
              </div>
              <button
                className="primary-button"
                type="button"
                onClick={handleCompare}
                disabled={!selectedItem || isComparing}
              >
                <span>{isComparing ? "Comparing" : "Compare"}</span>
              </button>
            </div>

            <label className="search-box">
              <span>Type name</span>
              <input
                value={query}
                onChange={handleQueryChange}
                placeholder="Tritanium, PLEX, Rifter"
              />
            </label>

            <div className="search-tools">
              <label>
                <span>Sort results</span>
                <select value={searchSort} onChange={(event) => setSearchSort(event.target.value)}>
                  <option value="name">Name</option>
                  <option value="type_id">Type ID</option>
                  <option value="market_group">Market group</option>
                </select>
              </label>
              <label className="check-row">
                <input
                  type="checkbox"
                  checked={marketOnly}
                  onChange={(event) => setMarketOnly(event.target.checked)}
                />
                <span>Market items only</span>
              </label>
            </div>

            <div className="search-results">
              {isSearching && <p className="muted">Searching...</p>}
              {!isSearching && !selectedItem && query.trim().length >= 2 && results.length === 0 && (
                <p className="muted">No matching items yet.</p>
              )}
              {!isSearching &&
                results.map((item) => (
                  <button
                    className="result-row"
                    key={item.type_id}
                    type="button"
                    onClick={() => selectItem(item)}
                  >
                    <span>{item.name}</span>
                    <code>{item.type_id}</code>
                  </button>
                ))}
            </div>
          </section>

          <MarketTable comparison={comparison} />
        </div>

        <aside className="watchlist-panel" aria-labelledby="watchlist-heading">
          <div className="panel-header">
            <div>
              <h2 id="watchlist-heading">Watchlist</h2>
              <p>
                {visibleWatchlist.length} of {watchlist.length} tracked items
              </p>
            </div>
          </div>

          <form className="watch-form" onSubmit={handleWatchSubmit}>
            <label>
              <span>Item</span>
              <input
                value={selectedWatchItem?.item_name ?? selectedItem?.name ?? ""}
                readOnly
                placeholder="Select from search"
              />
            </label>
            <label>
              <span>Target price</span>
              <input
                min="0"
                step="0.01"
                type="number"
                value={watchForm.target_price}
                onChange={(event) =>
                  setWatchForm((current) => ({
                    ...current,
                    target_price: event.target.value,
                  }))
                }
              />
            </label>
            <label>
              <span>Notes</span>
              <textarea
                value={watchForm.notes}
                rows="3"
                onChange={(event) =>
                  setWatchForm((current) => ({
                    ...current,
                    notes: event.target.value,
                  }))
                }
              />
            </label>
            <div className="form-actions">
              <button className="primary-button" type="submit" disabled={isSaving}>
                {editingId ? "Update" : "Add"}
              </button>
              {editingId && (
                <button className="ghost-button" type="button" onClick={cancelEdit}>
                  Cancel
                </button>
              )}
            </div>
          </form>

          <div className="watch-tools">
            <label>
              <span>Filter</span>
              <input
                value={watchFilter}
                onChange={(event) => setWatchFilter(event.target.value)}
                placeholder="Name or notes"
              />
            </label>
            <label>
              <span>Sort</span>
              <select value={watchSort} onChange={(event) => setWatchSort(event.target.value)}>
                <option value="name">Name</option>
                <option value="newest">Newest</option>
                <option value="target_desc">Target high</option>
                <option value="target_asc">Target low</option>
              </select>
            </label>
          </div>

          <div className="watchlist">
            {visibleWatchlist.length === 0 && <p className="muted">No watchlist items match.</p>}
            {visibleWatchlist.map((item) => (
              <article className="watch-item" key={item.id}>
                <div>
                  <strong>{item.item_name}</strong>
                  <span>Target {formatIsk(item.target_price)} ISK</span>
                </div>
                {item.notes && <p>{item.notes}</p>}
                <div className="row-actions">
                  <button type="button" onClick={() => beginEdit(item)}>
                    Edit
                  </button>
                  <button type="button" onClick={() => removeWatchItem(item.id)}>
                    Delete
                  </button>
                </div>
              </article>
            ))}
          </div>
        </aside>
      </section>

      {(status || error) && (
        <div className={`toast ${error ? "error" : ""}`} role="status">
          {error || status}
        </div>
      )}
    </main>
  );
}

function MarketTable({ comparison }) {
  const [sortKey, setSortKey] = useState("hub");
  const [hideMissing, setHideMissing] = useState(false);

  const rows = useMemo(() => {
    const baseRows = [
      { hub: "Jita", prices: comparison?.jita },
      { hub: "Amarr", prices: comparison?.amarr },
      { hub: "CJ", prices: comparison?.cj },
    ].map((row) => ({
      ...row,
      buy: row.prices?.buy,
      sell: row.prices?.sell,
      spread:
        row.prices?.buy !== null &&
        row.prices?.buy !== undefined &&
        row.prices?.sell !== null &&
        row.prices?.sell !== undefined
          ? Number(row.prices.sell) - Number(row.prices.buy)
          : null,
    }));

    const filteredRows = hideMissing
      ? baseRows.filter(
          (row) =>
            row.buy !== null &&
            row.buy !== undefined &&
            row.sell !== null &&
            row.sell !== undefined,
        )
      : baseRows;

    return [...filteredRows].sort((first, second) => {
      if (sortKey === "hub") {
        return first.hub.localeCompare(second.hub);
      }

      const firstValue = first[sortKey];
      const secondValue = second[sortKey];
      if (firstValue === null || firstValue === undefined) {
        return 1;
      }
      if (secondValue === null || secondValue === undefined) {
        return -1;
      }

      return Number(firstValue) - Number(secondValue);
    });
  }, [comparison, hideMissing, sortKey]);

  return (
    <section className="panel table-panel" aria-labelledby="compare-heading">
      <div className="panel-header">
        <div>
          <h2 id="compare-heading">Market Comparison</h2>
          <p>Highest buy and lowest sell</p>
        </div>
      </div>

      <div className="table-tools">
        <label>
          <span>Sort</span>
          <select value={sortKey} onChange={(event) => setSortKey(event.target.value)}>
            <option value="hub">Hub</option>
            <option value="buy">Buy low to high</option>
            <option value="sell">Sell low to high</option>
            <option value="spread">Spread low to high</option>
          </select>
        </label>
        <label className="check-row">
          <input
            type="checkbox"
            checked={hideMissing}
            onChange={(event) => setHideMissing(event.target.checked)}
          />
          <span>Hide missing prices</span>
        </label>
      </div>

      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Hub</th>
              <th>Buy</th>
              <th>Sell</th>
              <th>Spread</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr key={row.hub}>
                <td>{row.hub}</td>
                <td>{formatIsk(row.buy)}</td>
                <td>{formatIsk(row.sell)}</td>
                <td>{formatIsk(row.spread)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export default App;
