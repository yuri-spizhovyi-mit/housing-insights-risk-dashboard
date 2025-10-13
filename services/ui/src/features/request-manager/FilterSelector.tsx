interface FilterSelectorProps {
  data: string[];
  value: string;
  handleValueUpdate: (value: string) => void;
}

function FilterSelector({
  value,
  handleValueUpdate,
  data,
}: FilterSelectorProps) {
  return (
    <select
      name={value}
      value={value}
      onChange={(e) => handleValueUpdate(e.target.value)}
      className="bg-transparent focus:outline-none px-1 text-sm sm:text-sm w-full flex-2"
    >
      {data.map((val) => (
        <option key={val} value={val} className="bg-neutral-900">
          {val}
        </option>
      ))}
    </select>
  );
}

export default FilterSelector;
