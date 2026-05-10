import { useEffect, useRef, useState } from "react";
import { FilterDropdown, type FilterOption } from "./FilterDropdown";

export interface AppliedFilters {
  search: string;
  dateRange: string[];
  eventStatus: string[];
  themes: string[];
  perks: string[];
}

interface EventFilterBarProps {
  filters: AppliedFilters;
  onChange: (filters: AppliedFilters) => void;
}

function titleCase(s: string): string {
  return s
    .split(/[\s_]+/)
    .map((w) => (w ? w.charAt(0).toUpperCase() + w.slice(1).toLowerCase() : w))
    .join(" ");
}

const DATE_OPTIONS: FilterOption[] = [
  { value: "today", label: "Today" },
  { value: "week", label: "This Week" },
  { value: "month", label: "This Month" },
];

const STATUS_OPTIONS: FilterOption[] = [
  { value: "in-person", label: "In-Person" },
  { value: "virtual", label: "Virtual" },
  { value: "hybrid", label: "Hybrid" },
];

const THEME_VALUES = [
  "academic",
  "arts",
  "athletics",
  "career",
  "community",
  "cultural",
  "fundraising",
  "social",
  "spirituality",
];

const THEME_OPTIONS: FilterOption[] = THEME_VALUES.map((v) => ({
  value: v,
  label: titleCase(v),
}));

const PERK_VALUES = ["free_food", "free_stuff", "credit"];

const PERK_OPTIONS: FilterOption[] = PERK_VALUES.map((v) => ({
  value: v,
  label: titleCase(v),
}));

const SEARCH_DEBOUNCE_MS = 300;

export function EventFilterBar({ filters, onChange }: EventFilterBarProps) {
  const [searchInput, setSearchInput] = useState(filters.search);
  const debounceRef = useRef<number | undefined>(undefined);
  const lastEmittedRef = useRef(filters.search);

  useEffect(() => {
    if (filters.search !== lastEmittedRef.current) {
      setSearchInput(filters.search);
      lastEmittedRef.current = filters.search;
    }
  }, [filters.search]);

  function handleSearchChange(value: string) {
    setSearchInput(value);
    if (debounceRef.current !== undefined) {
      window.clearTimeout(debounceRef.current);
    }
    debounceRef.current = window.setTimeout(() => {
      lastEmittedRef.current = value;
      onChange({ ...filters, search: value });
    }, SEARCH_DEBOUNCE_MS);
  }

  function flushSearch() {
    if (debounceRef.current !== undefined) {
      window.clearTimeout(debounceRef.current);
      debounceRef.current = undefined;
    }
    if (searchInput !== lastEmittedRef.current) {
      lastEmittedRef.current = searchInput;
      onChange({ ...filters, search: searchInput });
    }
  }

  function clearSearch() {
    if (debounceRef.current !== undefined) {
      window.clearTimeout(debounceRef.current);
      debounceRef.current = undefined;
    }
    setSearchInput("");
    lastEmittedRef.current = "";
    onChange({ ...filters, search: "" });
  }

  function clearAllFilters() {
    setSearchInput("");
    lastEmittedRef.current = "";
    onChange({
      search: "",
      dateRange: [],
      eventStatus: [],
      themes: [],
      perks: [],
    });
  }

  const hasActiveFilters =
    filters.search ||
    filters.dateRange.length > 0 ||
    filters.eventStatus.length > 0 ||
    filters.themes.length > 0 ||
    filters.perks.length > 0;

  return (
    <div className="filter-bar" role="toolbar" aria-label="Event filters">
      <FilterDropdown
        label="Date"
        options={DATE_OPTIONS}
        selected={filters.dateRange}
        multi={false}
        onApply={(values) => onChange({ ...filters, dateRange: values })}
        defaultLabel="All upcoming"
      />
      <div className="filter-bar__search">
        <svg
          className="filter-bar__search-icon"
          width="16"
          height="16"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <circle cx="11" cy="11" r="7" />
          <line x1="20" y1="20" x2="16.65" y2="16.65" />
        </svg>
        <input
          type="search"
          className="filter-bar__search-input"
          placeholder="Search events..."
          value={searchInput}
          onChange={(e) => handleSearchChange(e.target.value)}
          onBlur={flushSearch}
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              flushSearch();
            }
          }}
          aria-label="Search events"
        />
        {searchInput && (
          <button
            type="button"
            className="filter-bar__search-clear"
            onClick={clearSearch}
            aria-label="Clear search"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
              aria-hidden="true"
            >
              <line x1="18" y1="6" x2="6" y2="18" />
              <line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        )}
      </div>
      <FilterDropdown
        label="Status"
        options={STATUS_OPTIONS}
        selected={filters.eventStatus}
        multi={false}
        onApply={(values) => onChange({ ...filters, eventStatus: values })}
      />
      <FilterDropdown
        label="Theme"
        options={THEME_OPTIONS}
        selected={filters.themes}
        multi={true}
        onApply={(values) => onChange({ ...filters, themes: values })}
      />
      <FilterDropdown
        label="Perks"
        options={PERK_OPTIONS}
        selected={filters.perks}
        multi={true}
        onApply={(values) => onChange({ ...filters, perks: values })}
      />
      {hasActiveFilters && (
        <button
          type="button"
          className="filter-bar__clear-btn"
          onClick={clearAllFilters}
          aria-label="Clear all filters"
        >
          Clear Filters
        </button>
      )}
    </div>
  );
}
