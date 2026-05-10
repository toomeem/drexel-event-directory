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
}

export function FilterDropdown({
  label,
  options,
  selected,
  multi,
  onApply,
  defaultLabel = "All",
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
  const buttonLabel = !isActive
    ? label
    : multi
      ? `${label} (${selected.length})`
      : `${label}: ${options.find((o) => o.value === selected[0])?.label ?? selected[0]}`;

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
    onApply(draft);
    setOpen(false);
  }

  function clearAll() {
    if (multi) {
      onApply([]);
      setOpen(false);
    } else {
      onApply([]);
      setOpen(false);
    }
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
