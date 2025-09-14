package maxdev.env.model.macro;

import lombok.*;
import java.io.Serializable;
import java.time.LocalDate;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class MacroEconomicDataId implements Serializable {
    private LocalDate date;
    private String province;
}
