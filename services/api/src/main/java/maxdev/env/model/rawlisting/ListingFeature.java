package maxdev.env.model.rawlisting;

import jakarta.persistence.*;
import lombok.*;
import java.math.BigDecimal;
import java.time.OffsetDateTime;

@Entity
@Table(
    name = "listings_features",
    indexes = {
        @Index(
            name = "idx_lf_postal_bedrooms", 
            columnList = "postal_code,bedrooms"
        ),
        @Index(
            name = "idx_lf_postal", 
            columnList = "postal_code"
        ),
        @Index(
            name = "idx_lf_price_per_sqft", 
            columnList = "price_per_sqft"
        )
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ListingFeature {
    @Id
    @Column(name = "listing_id", length = 255, nullable = false)
    private String id;

    @Column(name = "price_per_sqft", precision = 12, scale = 2)
    private BigDecimal pricePerSqft;

    @Column(name = "property_age")
    private Integer propertyAge;

    @Column(name = "bedrooms")
    private Integer bedrooms;

    @Column(name = "bathrooms")
    private Integer bathrooms;

    @Column(name = "area_sqft")
    private Integer areaSqft;

    @Column(name = "year_built")
    private Integer yearBuilt;

    @Column(name = "postal_code", length = 20)
    private String postalCode;

    @Column(name = "property_type_house")
    private Boolean propertyTypeHouse;

    @Column(name = "property_type_condo")
    private Boolean propertyTypeCondo;

    @Column(name = "property_type_apartment")
    private Boolean propertyTypeApartment;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @Column(name = "updated_at", nullable = false)
    private OffsetDateTime updatedAt;

    @PrePersist
    void onCreate() {
        var now = OffsetDateTime.now();
        this.createdAt = now;
        this.updatedAt = now;
    }

    @PreUpdate
    void onUpdate() {
        this.updatedAt = OffsetDateTime.now();
    }
}
