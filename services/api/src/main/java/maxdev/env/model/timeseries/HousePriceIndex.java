package maxdev.env.model.timeseries;

import jakarta.persistence.*;
import lombok.*;

import java.math.BigDecimal;
import java.time.LocalDate;

@Entity
@Table(
    name = "house_price_index",
    indexes = {
        @Index(name = "idx_hpi_city_date", columnList = "city,date"),
        @Index(name = "idx_hpi_city", columnList = "city"),
        @Index(name = "idx_hpi_date", columnList = "date")
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@IdClass(HousePriceIndexId.class) 
public class HousePriceIndex {
    @Id
    @Column(name = "date", nullable = false)
    private LocalDate date;

    @Id
    @Column(name = "city", length = 100, nullable = false)
    private String city;

    @Column(name = "index_value", precision = 10, scale = 2, nullable = false)
    private BigDecimal indexValue;

    @Column(name = "median_price_house", precision = 12, scale = 2)
    private BigDecimal medianPriceHouse;

    @Column(name = "median_price_condo", precision = 12, scale = 2)
    private BigDecimal medianPriceCondo;

    @Column(name = "active_listings_count")
    private Integer activeListingsCount;

    @Column(name = "avg_listing_days")
    private Integer avgListingDays;
}
