import {useEffect, useRef, useState} from "react";
import {FilterDropdown, type FilterOption} from "./FilterDropdown";
import {FilterOptionGroup} from "./FilterOptionGroup";

export interface AppliedFilters {
    search: string;
    dateRange: string[];
    eventStatus: string[];
    themes: string[];
    perks: string[];
    foodRelated: boolean;
    popular: boolean;
    recurring: boolean;
    forNewStudents: boolean;
    onCampus: boolean;
    religion: string[];
}

interface EventFilterBarProps {
    filters: AppliedFilters;
    onChange: (filters: AppliedFilters) => void;
}

interface EventTopFilterBarProps extends EventFilterBarProps {
    totalEvents: number;
}

const DATE_OPTIONS: FilterOption[] = [
    {value: "today", label: "Today"},
    {value: "week", label: "This Week"},
    {value: "month", label: "This Month"},
];

const STATUS_OPTIONS: FilterOption[] = [
    {value: "in-person", label: "In-Person"},
    {value: "online", label: "Online"},
    {value: "hybrid", label: "Hybrid"},
];

const THEME_OPTIONS: FilterOption[] = [
    {value: "academic", label: "Academic 📚"},
    {value: "arts", label: "Arts 🎭"},
    {value: "athletics", label: "Athletics ⚽"},
    {value: "career", label: "Career 👔"},
    {value: "cultural", label: "Cultural 🌎"},
    {value: "health", label: "Health 🩺"},
    {value: "fundraising", label: "Fundraising 💸"},
    {value: "social", label: "Social 🗪"},
    {value: "spirituality", label: "Spirituality 🙏"},
];

const PERK_OPTIONS: FilterOption[] = [
    {value: "free_food", label: "Free Food 🍔"},
    {value: "giveaway", label: "Giveaway 🎁"},
    {value: "free_stuff", label: "Free Stuff 🛍️"},
    {value: "prizes", label: "Prizes 🥇"},
    {value: "credit", label: "Credit 🎟️"},
];

const RELIGION_OPTIONS: FilterOption[] = [
    {value: "christian", label: "Christian ✞"},
    {value: "jewish", label: "Jewish ✡︎"},
    {value: "muslim", label: "Muslim ☪︎"},
    {value: "hindu", label: "Hindu ॐ"},
];

const SEARCH_DEBOUNCE_MS = 300;

export function EventFilterBar({
                                   filters,
                                   totalEvents,
                                   onChange,
                               }: EventTopFilterBarProps) {
    const [searchInput, setSearchInput] = useState(filters.search);
    const debounceRef = useRef<number | undefined>(undefined);
    const lastEmittedRef = useRef(filters.search);
    const resultLabel = totalEvents === 1 ? "result" : "results";

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
            onChange({...filters, search: value});
        }, SEARCH_DEBOUNCE_MS);
    }

    function flushSearch() {
        if (debounceRef.current !== undefined) {
            window.clearTimeout(debounceRef.current);
            debounceRef.current = undefined;
        }
        if (searchInput !== lastEmittedRef.current) {
            lastEmittedRef.current = searchInput;
            onChange({...filters, search: searchInput});
        }
    }

    function clearSearch() {
        if (debounceRef.current !== undefined) {
            window.clearTimeout(debounceRef.current);
            debounceRef.current = undefined;
        }
        setSearchInput("");
        lastEmittedRef.current = "";
        onChange({...filters, search: ""});
    }

    return (
        <div className="filter-bar" role="toolbar" aria-label="Event filters">
            <FilterDropdown
                label="Date"
                options={DATE_OPTIONS}
                selected={filters.dateRange}
                multi={false}
                onApply={(values) => onChange({...filters, dateRange: values})}
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
                    <circle cx="11" cy="11" r="7"/>
                    <line x1="20" y1="20" x2="16.65" y2="16.65"/>
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
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                )}
            </div>
            <p className="filter-bar__result-count">
                {totalEvents.toLocaleString()} {resultLabel}
            </p>
        </div>
    );
}

export function EventSidebarFilters({filters, onChange}: EventFilterBarProps) {
    const [open, setOpen] = useState(false);
    const boolFilterCount = [
        filters.foodRelated,
        filters.popular,
        filters.recurring,
        filters.forNewStudents,
        filters.onCampus,
    ].filter(Boolean).length;
    const hasActiveFilters =
        filters.eventStatus.length > 0 ||
        filters.themes.length > 0 ||
        filters.perks.length > 0 ||
        filters.religion.length > 0 ||
        boolFilterCount > 0;
    const activeFilterCount =
        filters.eventStatus.length +
        filters.themes.length +
        filters.perks.length +
        filters.religion.length +
        boolFilterCount;

    function clearFilters() {
        onChange({
            ...filters,
            eventStatus: [],
            themes: [],
            perks: [],
            foodRelated: false,
            popular: false,
            recurring: false,
            forNewStudents: false,
            onCampus: false,
            religion: [],
        });
    }

    return (
        <aside
            className={
                "event-filter-sidebar" + (open ? " event-filter-sidebar--open" : "")
            }
            aria-label="Additional filters"
        >
            <button
                type="button"
                className="event-filter-sidebar__toggle"
                onClick={() => setOpen((value) => !value)}
                aria-expanded={open}
                aria-controls="event-filter-sidebar-content"
            >
        <span className="event-filter-sidebar__toggle-label">
          Filters
            {activeFilterCount > 0 && (
                <span className="event-filter-sidebar__toggle-badge">
              {activeFilterCount}
            </span>
            )}
        </span>
                <svg
                    className="event-filter-sidebar__toggle-chevron"
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
                    <polyline points="6 9 12 15 18 9"/>
                </svg>
            </button>
            <div
                id="event-filter-sidebar-content"
                className="event-filter-sidebar__content"
            >
                <div className="sidebar-filter-section">
                    <div className="filter-option-group filter-option-group--flat" role="group"
                         aria-label="Special filters">
                        <ul className="filter-option-group__options">
                            {(
                                [
                                    {key: "foodRelated", label: "Food Related🍔"},
                                    {key: "popular", label: "Popular🔥"},
                                    {key: "recurring", label: "Recurring 🔁"},
                                    {key: "forNewStudents", label: "For New Students🎉"},
                                    {key: "onCampus", label: "On Campus📍"},
                                ] as { key: keyof AppliedFilters; label: string }[]
                            ).map(({key, label}, index) => {
                                const checked = filters[key] as boolean;
                                return (
                                    <li
                                        key={key}
                                        className={
                                            index === 0
                                                ? "filter-option-group__item--has-clear"
                                                : undefined
                                        }
                                    >
                                        <label
                                            className={
                                                "filter-option-group__option" +
                                                (checked ? " filter-option-group__option--selected" : "")
                                            }
                                        >
                                            <input
                                                type="checkbox"
                                                className="filter-option-group__input"
                                                checked={checked}
                                                onChange={() => onChange({...filters, [key]: !checked})}
                                            />
                                            <span>{label}</span>
                                        </label>
                                        {index === 0 && (
                                            <button
                                                type="button"
                                                className="event-filter-sidebar__clear"
                                                onClick={clearFilters}
                                                disabled={!hasActiveFilters}
                                            >
                                                Clear
                                            </button>
                                        )}
                                    </li>
                                );
                            })}
                        </ul>
                    </div>
                </div>
                <div className="sidebar-filter-section">
                    <p className="sidebar-filter-section__label" id="filter-status-label">
                        Status
                    </p>
                    <FilterOptionGroup
                        label="Status"
                        options={STATUS_OPTIONS}
                        selected={filters.eventStatus}
                        onSelect={(values) => onChange({...filters, eventStatus: values})}
                        labelledBy="filter-status-label"
                    />
                </div>
                <div className="sidebar-filter-section">
                    <p className="sidebar-filter-section__label" id="filter-perks-label">
                        Perks
                    </p>
                    <FilterOptionGroup
                        label="Perks"
                        options={PERK_OPTIONS}
                        selected={filters.perks}
                        multi={true}
                        onSelect={(values) => onChange({...filters, perks: values})}
                        labelledBy="filter-perks-label"
                        initialVisibleCount={2}
                    />
                </div>
                <div className="sidebar-filter-section">
                    <div className="sidebar-filter-section__header">
                        <p className="sidebar-filter-section__label" id="filter-theme-label">
                            Theme
                        </p>
                        <button
                            type="button"
                            className="filter-option-group__select-all"
                            onClick={() =>
                                onChange({
                                    ...filters,
                                    themes:
                                        filters.themes.length === THEME_OPTIONS.length
                                            ? []
                                            : THEME_OPTIONS.map((o) => o.value),
                                })
                            }
                        >
                            {filters.themes.length === THEME_OPTIONS.length
                                ? "Deselect all"
                                : "Select all"}
                        </button>
                    </div>
                    <FilterOptionGroup
                        label="Event Type"
                        options={THEME_OPTIONS}
                        selected={filters.themes}
                        multi={true}
                        onSelect={(values) => onChange({...filters, themes: values})}
                        labelledBy="filter-theme-label"
                        initialVisibleCount={4}
                    />
                </div>
                <div className="sidebar-filter-section">
                    <p className="sidebar-filter-section__label" id="filter-religion-label">
                        Religion
                    </p>
                    <FilterOptionGroup
                        label="Religion"
                        options={RELIGION_OPTIONS}
                        selected={filters.religion}
                        multi={true}
                        onSelect={(values) => onChange({...filters, religion: values})}
                        labelledBy="filter-religion-label"
                    />
                </div>
            </div>
        </aside>
    );
}
