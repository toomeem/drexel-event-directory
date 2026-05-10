import { FilterDropdown, type FilterOption } from "./FilterDropdown";

export interface AppliedFilters {
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

export function EventFilterBar({ filters, onChange }: EventFilterBarProps) {
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
    </div>
  );
}
