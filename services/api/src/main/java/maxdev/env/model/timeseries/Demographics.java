package maxdev.env.model.timeseries;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(
    name = "demographics",
    indexes = {
        @Index(name = "idx_demo_city_date", columnList = "city,date"),
        @Index(name = "idx_demo_city", columnList = "city"),
        @Index(name = "idx_demo_date", columnList = "date")
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@IdClass(DemographicsId.class)
public class Demographics {

    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Id
    @Column(name = "city", length = 100, nullable = false)
    private String city;

    @Column(name = "population")
    private Integer population;

    @Column(name = "net_migration")
    private Integer netMigration;

    @Column(name = "age_distribution_25_34_perc", precision = 5, scale = 2)
    private BigDecimal ageDistribution25to34Perc;

    @Column(name = "avg_disposable_income", precision = 12, scale = 2)
    private BigDecimal avgDisposableIncome;
}
