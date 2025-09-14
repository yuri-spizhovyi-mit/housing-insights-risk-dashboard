package maxdev.env.model.rawlisting;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;

@Entity
@Table(
    name = "construction_permits",
    indexes = {
        @Index(name = "idx_cp_city_date", columnList = "city,date_approved"),
        @Index(name = "idx_cp_postal_code", columnList = "postal_code")
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ConstructionPermit {
    @Id
    @Column(name = "permit_id", length = 255, nullable = false)
    private String permitId;

    @Column(name = "city", length = 100)
    private String city;

    @Column(name = "postal_code", length = 20)
    private String postalCode;

    @Column(name = "units_approved")
    private Integer unitsApproved;

    @Column(name = "date_approved")
    private LocalDate dateApproved;

    @Column(name = "property_type", length = 50)
    private String propertyType;
}
