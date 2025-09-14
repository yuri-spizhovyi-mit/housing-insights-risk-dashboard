package maxdev.env.model.timeseries;

import lombok.*;
import java.io.Serializable;
import java.time.LocalDate;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class HousePriceIndexId implements Serializable {
    private LocalDate date;
    private String city;
}
