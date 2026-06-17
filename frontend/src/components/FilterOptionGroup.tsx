import { useState } from "react";
import type { FilterOption } from "./FilterDropdown";

interface FilterOptionGroupProps {
  label: string;
  options: FilterOption[];
  selected: string[];
  onSelect: (values: string[]) => void;
  labelledBy?: string;
  multi?: boolean;
  initialVisibleCount?: number;
}

export function FilterOptionGroup({
  label,
  options,
  selected,
  onSelect,
  labelledBy,
  multi = false,
  initialVisibleCount,
}: FilterOptionGroupProps) {
  const [expanded, setExpanded] = useState(false);
  const groupName = `filter-${label.toLowerCase().replace(/\s+/g, "-")}`;

  const canCollapse =
    initialVisibleCount !== undefined && options.length > initialVisibleCount;
  const visibleOptions =
    canCollapse && !expanded ? options.slice(0, initialVisibleCount) : options;

  function handleChange(value: string) {
    onSelect([value]);
  }

  function handleClick(isSelected: boolean) {
    if (isSelected) {
      onSelect([]);
    }
  }

  function handleToggle(value: string, isSelected: boolean) {
    if (isSelected) {
      onSelect(selected.filter((v) => v !== value));
    } else {
      onSelect([...selected, value]);
    }
  }

  return (
    <div
      className="filter-option-group"
      role={multi ? "group" : "radiogroup"}
      aria-label={labelledBy ? undefined : label}
      aria-labelledby={labelledBy}
    >
      <ul className="filter-option-group__options">
        {visibleOptions.map((option) => {
          const isSelected = multi
            ? selected.includes(option.value)
            : selected[0] === option.value;
          return (
            <li key={option.value}>
              <label
                className={
                  "filter-option-group__option" +
                  (isSelected ? " filter-option-group__option--selected" : "")
                }
              >
                {multi ? (
                  <input
                    type="checkbox"
                    className="filter-option-group__input"
                    checked={isSelected}
                    onChange={() => handleToggle(option.value, isSelected)}
                  />
                ) : (
                  <input
                    type="radio"
                    name={groupName}
                    className="filter-option-group__input"
                    checked={isSelected}
                    onChange={() => handleChange(option.value)}
                    onClick={() => handleClick(isSelected)}
                  />
                )}
                <span>{option.label}</span>
              </label>
            </li>
          );
        })}
      </ul>
      {canCollapse && (
        <button
          type="button"
          className="filter-option-group__toggle"
          onClick={() => setExpanded((v) => !v)}
        >
          {expanded
            ? "Show less"
            : `Show ${options.length - initialVisibleCount!} more`}
        </button>
      )}
    </div>
  );
}
