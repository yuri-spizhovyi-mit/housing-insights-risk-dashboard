package maxdev.env.model.predictions;

import lombok.*;
import jakarta.persistence.*;
import java.util.UUID;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.OffsetDateTime;

@Entity
@Table(
    name = "model_predictions",
    indexes = {
        @Index(
            name = "idx_mp_city_date", 
            columnList = "city,predict_date"
        ),
        @Index(
            name = "idx_mp_city", 
            columnList = "city"
        ),
        @Index(
            name = "idx_mp_created_at", 
            columnList = "created_at"
        )
    }
)
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class ModelPrediction {
    @Id
    @Column(name = "run_id", nullable = false, updatable = false)
    private UUID id;

    @Lob
    @Column(name = "model_name", nullable = false, columnDefinition = "text")
    private String modelName;

    @Lob
    @Column(name = "target", nullable = false, columnDefinition = "text")
    private String target;
    @Column(name = "horizon_months", nullable = false)
    private Integer horizonMonths;

    @Column(name = "city", nullable = false, length = 100)
    private String city;

    @Column(name = "predict_date", nullable = false)
    private LocalDate predictDate;

    @Column(name = "yhat", precision = 14, scale = 4, nullable = false)
    private BigDecimal yhat;

    @Column(name = "yhat_lower", precision = 14, scale = 4, nullable = false)
    private BigDecimal yhatLower;

    @Column(name = "yhat_upper", precision = 14, scale = 4, nullable = false)
    private BigDecimal yhatUpper;

    @Lob
    @Column(name = "features_version", columnDefinition = "text")
    private String featuresVersion;

    @Lob
    @Column(name = "model_artifact_uri", columnDefinition = "text")
    private String modelArtifactUri;

    @Column(name = "created_at", nullable = false, updatable = false)
    private OffsetDateTime createdAt;

    @PrePersist
    void onCreate() {
        this.createdAt = OffsetDateTime.now();
    }
}
