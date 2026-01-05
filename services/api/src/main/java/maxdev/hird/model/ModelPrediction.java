package maxdev.hird.model;


import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(
        name = "model_predictions",
        indexes = {
                @Index(
                        name = "idx_pred_city_target_model_horizon_date",
                        columnList = "city, target, model_name, horizon_months, predict_date"
                )
        }
)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class ModelPrediction {
    @Id
    @GeneratedValue
    @Column(name="run_id")
    private UUID id;

    @Column(name="horizon_months")
    private Integer horizonMonths;

    @Column(name="predict_date")
    private LocalDate predictDate;

    private String city;
    private String target;

    @Column(name = "model_name", nullable = false)
    private String modelName;

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

    @Column(name="year_built_min")
    private Integer yearBuiltMin;

    @Column(name="year_built_max")
    private Integer yearBuiltMax;
}

