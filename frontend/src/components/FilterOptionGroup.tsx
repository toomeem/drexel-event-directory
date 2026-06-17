import type { FilterOption } from "./FilterDropdown";

interface FilterOptionGroupProps {
  label: string;
  options: FilterOption[];
  selected: string[];
  onSelect: (values: string[]) => void;
  labelledBy?: string;
}

export function FilterOptionGroup({
  label,
  options,
  selected,
  onSelect,
  labelledBy,
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

  return (
    <div
      className="filter-option-group"
      role="radiogroup"
      aria-label={labelledBy ? undefined : label}
      aria-labelledby={labelledBy}
    >
      <ul className="filter-option-group__options">
        {options.map((option) => {
          const isSelected = selected[0] === option.value;
          return (
            <li key={option.value}>
              <label
                className={
                  "filter-option-group__option" +
                  (isSelected ? " filter-option-group__option--selected" : "")
                }
              >
                <input
                  type="radio"
                  name={groupName}
                  className="filter-option-group__input"
                  checked={isSelected}
                  onChange={() => handleChange(option.value)}
                  onClick={() => handleClick(isSelected)}
                />
                <span>{option.label}</span>
              </label>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
