import type { FilterOption } from "./FilterDropdown";

interface FilterOptionGroupProps {
  label: string;
  options: FilterOption[];
  selected: string[];
  onSelect: (values: string[]) => void;
  labelledBy?: string;
  multi?: boolean;
}

export function FilterOptionGroup({
  label,
  options,
  selected,
  onSelect,
  labelledBy,
  multi = false,
}: FilterOptionGroupProps) {
  const groupName = `filter-${label.toLowerCase().replace(/\s+/g, "-")}`;

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
        {options.map((option) => {
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
    </div>
  );
}
