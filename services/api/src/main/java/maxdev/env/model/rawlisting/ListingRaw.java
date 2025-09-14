package maxdev.env.model.rawlisting;

import java.math.BigDecimal;
import java.sql.Date;

import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.Id;
import jakarta.persistence.Index;
import jakarta.persistence.Lob;
import jakarta.persistence.Table;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;


@Entity
@Table(
    name = "listings_raw",
    indexes = {
        @Index(
            name = "idx_listings_raw_city_date",
            columnList = "city,date_posted"
        ),
        @Index(
            name = "idx_listings_raw_city",
            columnList = "city"
        ),
        @Index(
            name = "idx_listings_raw_postal_code",
            columnList = "postal_code"
        )
    }
)
@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class ListingRaw {
    @Id
    @Column(name = "listing_id", length = 255, nullable = false)
    private String id;
    
    @Lob
    @Column(name = "url", nullable = false, length = 255)
    private String url;

    @Column(name = "date_posted", nullable = false)
    private Date datePosted;

    @Column(name = "city", length = 100, nullable = false)
    private String city;
    
    @Column(name = "postal_code", length = 20)
    private String postalCode;
    
    @Column(name = "property_type", length = 50)
    private String propertyType;

    @Column(name = "price", precision = 12, scale = 2)
    private BigDecimal price;

    private Integer bedrooms;
    private Integer bathrooms;
    
    @Column(name="area_sqrt")
    private Integer areaSqrt;
    
    @Column(name = "year_built")
    private Integer yearBuilt;

    @Lob
    @Column(name = "description", columnDefinition = "text")
    private String description;
} 