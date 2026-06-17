import { useEffect, useRef, useState } from "react";

export interface FilterOption {
  value: string;
  label: string;
}

interface FilterDropdownProps {
  label: string;
  options: FilterOption[];
  selected: string[];
  multi: boolean;
  onApply: (values: string[]) => void;
  defaultLabel?: string;
  showLabel?: boolean;
}

export function FilterDropdown({
  label,
  options,
  selected,
  multi,
  onApply,
  defaultLabel = "All",
  showLabel = true,
}: FilterDropdownProps) {
  const [open, setOpen] = useState(false);
  const [draft, setDraft] = useState<string[]>(selected);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setDraft(selected);
  }, [selected, open]);

  useEffect(() => {
    if (!open) return;
    function onMouseDown(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    }
    function onKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("mousedown", onMouseDown);
    document.addEventListener("keydown", onKeyDown);
    return () => {
      document.removeEventListener("mousedown", onMouseDown);
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const isActive = selected.length > 0;
  const optionValues = options.map((o) => o.value);
  const allOptionsSelected =
    optionValues.length > 0 && optionValues.every((value) => draft.includes(value));
  const buttonLabel = showLabel
    ? !isActive
      ? label
      : multi
        ? selected.length === options.length
          ? `${label} (All)`
          : `${label} (${selected.length})`
        : `${label}: ${options.find((o) => o.value === selected[0])?.label ?? selected[0]}`
    : !isActive
      ? defaultLabel
      : multi
        ? selected.length === options.length
          ? defaultLabel
          : `${selected.length} selected`
        : options.find((o) => o.value === selected[0])?.label ?? selected[0];

  function toggleSingle(value: string) {
    onApply(selected[0] === value ? [] : [value]);
    setOpen(false);
  }

  function toggleMulti(value: string) {
    setDraft((d) =>
      d.includes(value) ? d.filter((v) => v !== value) : [...d, value],
    );
  }

  function applyMulti() {
    onApply(allOptionsSelected ? [] : draft);
    setOpen(false);
  }

  function clearAll() {
    onApply([]);
    setOpen(false);
  }

  function toggleAllMulti() {
    setDraft(allOptionsSelected ? [] : optionValues);
  }

  return (
    <div className="filter-dropdown" ref={containerRef}>
      <button
        type="button"
        className={
          "filter-dropdown__btn" +
          (isActive ? " filter-dropdown__btn--active" : "") +
          (open ? " filter-dropdown__btn--open" : "")
        }
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
      >
        <span>{buttonLabel}</span>
        <svg
          className="filter-dropdown__chevron"
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>
      {open && (
        <div className="filter-dropdown__panel" role="listbox">
          <ul className="filter-dropdown__options">
            <li>
              {multi ? (
                <button
                  type="button"
                  className={
                    "filter-dropdown__option filter-dropdown__option--default" +
                    (allOptionsSelected ? " filter-dropdown__option--selected" : "")
                  }
                  onClick={toggleAllMulti}
                  disabled={options.length === 0}
                >
                  {allOptionsSelected ? "Unselect All" : "Select All"}
                </button>
              ) : (
                <button
                  type="button"
                  className={
                    "filter-dropdown__option filter-dropdown__option--default" +
                    (selected.length === 0
                      ? " filter-dropdown__option--selected"
                      : "")
                  }
                  onClick={clearAll}
                >
                  {defaultLabel}
                </button>
              )}
            </li>
            {options.length === 0 && (
              <li className="filter-dropdown__empty">No options available</li>
            )}
            {options.map((o) => {
              const checked = multi
                ? draft.includes(o.value)
                : selected[0] === o.value;
              return (
                <li key={o.value}>
                  <label
                    className={
                      "filter-dropdown__option" +
                      (checked ? " filter-dropdown__option--selected" : "")
                    }
                  >
                    <input
                      type={multi ? "checkbox" : "radio"}
                      className="filter-dropdown__input"
                      checked={checked}
                      onChange={() =>
                        multi ? toggleMulti(o.value) : toggleSingle(o.value)
                      }
                    />
                    <span>{o.label}</span>
                  </label>
                </li>
              );
            })}
          </ul>
          {multi && (
            <div className="filter-dropdown__footer">
              <button
                type="button"
                className="filter-dropdown__apply"
                onClick={applyMulti}
              >
                Apply
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
