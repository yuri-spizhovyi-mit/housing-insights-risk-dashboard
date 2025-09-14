package maxdev.env.model.timeseries;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(
    name = "rent_index",
    indexes = {
        @Index(name = "idx_ri_city_date", columnList = "city,date"),
        @Index(name = "idx_ri_city", columnList = "city"),
        @Index(name = "idx_ri_date", columnList = "date")
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@IdClass(RentIndexId.class)
public class RentIndex {

    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Id
    @Column(name = "city", length = 100, nullable = false)
    private String city;

    @Column(name = "index_value", precision = 10, scale = 2, nullable = false)
    private BigDecimal indexValue;

    @Column(name = "median_rent_apartment_1br", precision = 12, scale = 2)
    private BigDecimal medianRentApartment1br;

    @Column(name = "median_rent_apartment_2br", precision = 12, scale = 2)
    private BigDecimal medianRentApartment2br;

    @Column(name = "median_rent_apartment_3br", precision = 12, scale = 2)
    private BigDecimal medianRentApartment3br;

    @Column(name = "active_rental_count")
    private Integer activeRentalCount;

    @Column(name = "avg_rental_days")
    private Integer avgRentalDays;
}
