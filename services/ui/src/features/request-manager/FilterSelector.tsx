// import { CheckIcon, ChevronDownIcon, ChevronUpIcon } from "lucide-react";
// import * as Select from "@radix-ui/react-select";
// import { forwardRef, type ReactNode } from "react";
// import { useLenis } from "../../context/useLenis";

import type { RequestModelType } from "../../context/FilterContext";

interface FilterSelectorProps {
  data: string[];
  value: string;
  handleValueUpdate: (value: string | RequestModelType) => void;
}

function FilterSelector({
  value,
  handleValueUpdate,
  data,
}: FilterSelectorProps) {
  // const lenis = useLenis();

  // const handleOpenChange = (open: boolean) =>
  //   open ? lenis.stop() : lenis.start();

  return (
    // <Select.Root
    //   value={value}
    //   onValueChange={handleValueUpdate}
    //   onOpenChange={handleOpenChange}
    // >
    //   <Select.Trigger
    //     className="
    //     overflow-x-hidden
    //     flex items-center justify-between w-full
    //     min-w-30 flex-1 h-7  rounded-xl
    //     bg-transparent text-sm text-primary
    //     focus:outline-none ml-3
    //     "
    //     aria-label="Filter"
    //   >
    //     <Select.Value placeholder="Select…" />
    //     <Select.Icon className="SelectIcon text-neutral-400">
    //       <ChevronDownIcon size={16} />
    //     </Select.Icon>
    //   </Select.Trigger>

    //   <Select.Portal>
    //     <Select.Content
    //       position="item-aligned"
    //       side="bottom"
    //       sideOffset={0}
    //       className="bg-surface-1 text-primary border border-neutral-700 rounded-lg shadow-lg"
    //     >
    //       <Select.ScrollUpButton className="flex justify-center p-1 text-neutral-500">
    //         <ChevronUpIcon size={14} />
    //       </Select.ScrollUpButton>

    //       <Select.Viewport className="p-2">
    //         <Select.Group>
    //           {data.map((val) => (
    //             <SelectItem key={val} value={val}>
    //               {val}
    //             </SelectItem>
    //           ))}
    //         </Select.Group>
    //       </Select.Viewport>
    //     </Select.Content>
    //   </Select.Portal>
    // </Select.Root>
    <select
      name={value}
      value={value}
      onChange={(e) => handleValueUpdate(e.target.value)}
      className="bg-transparent focus:outline-none px-1 text-sm sm:text-sm w-full flex-1"
    >
      {data.map((val) => (
        <option key={val} value={val}>
          {val}
        </option>
      ))}
    </select>
  );
}

// interface SelectItemProps {
//   children: ReactNode;
//   className?: string;
//   value: string;
// }

// const SelectItem = forwardRef<HTMLDivElement, SelectItemProps>(
//   ({ children, className, value }, forwardedRef) => {
//     return (
//       <Select.Item
//         className={`
//           ${className ?? ""}
//           text-sm rounded-md px-3 py-2 cursor-pointer
//           hover:bg-surface-2 focus:bg-surface-2
//           flex items-center justify-between gap-2
//           outline-none select-none
//         `}
//         value={value}
//         ref={forwardedRef}
//       >
//         <Select.ItemText>{children}</Select.ItemText>
//         <Select.ItemIndicator className="SelectItemIndicator text-emerald-500">
//           <CheckIcon size={14} />
//         </Select.ItemIndicator>
//       </Select.Item>
//     );
//   }
// );

export default FilterSelector;
