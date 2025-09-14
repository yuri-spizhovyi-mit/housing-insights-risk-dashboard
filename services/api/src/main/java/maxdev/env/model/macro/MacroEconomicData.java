package maxdev.env.model.macro;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(
    name = "macro_economic_data",
    indexes = {
        @Index(name = "idx_med_province_date", columnList = "province,date"),
        @Index(name = "idx_med_province", columnList = "province"),
        @Index(name = "idx_med_date", columnList = "date")
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@IdClass(MacroEconomicDataId.class)
public class MacroEconomicData {
    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Id
    @Column(name = "province", length = 100, nullable = false)
    private String province;

    @Column(name = "unemployment_rate", precision = 5, scale = 2)
    private BigDecimal unemploymentRate;

    @Column(name = "gdp_growth_rate", precision = 5, scale = 2)
    private BigDecimal gdpGrowthRate;

    @Column(name = "prime_lending_rate", precision = 5, scale = 2)
    private BigDecimal primeLendingRate;

    @Column(name = "housing_starts")
    private Integer housingStarts;
}
