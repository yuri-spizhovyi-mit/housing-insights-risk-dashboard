package hird.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class ModelPrediction {
    @Id
    @GeneratedValue
    private UUID run_id;

    @Column(name="horizon_months")
    private Integer horizonMonths;

    @Column(name="predicate_date")
    private LocalDate predictDate;

    private String city;
    private String target;

    @Column(name="yhat")
    private Double yhat;

    @Column(name="yhat_lower")
    private Double yhatLower;

    @Column(name="yhat_upper")
    private Double yhatUpper;

    @Column(name="property_type")
    private String propertyType;
    private Integer beds;
    private Integer baths;

    @Column(name="sqft_min")
    private Integer sqftMin;

    @Column(name="sqft_max")
    private Integer sqftMax;

    @Column(name="year_build_min")
    private Integer yearBuiltMin;

    @Column(name="year_build_max")
    private Integer yearBuiltMax;
}
