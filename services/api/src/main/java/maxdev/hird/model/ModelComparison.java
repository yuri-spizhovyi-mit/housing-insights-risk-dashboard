package maxdev.hird.model;

import jakarta.persistence.*;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.Setter;
import org.hibernate.annotations.CreationTimestamp;
import java.time.OffsetDateTime;

@Entity
@Table(
        name = "model_comparison",
        indexes = {
                @Index(
                        name = "idx_mc_model_horizon",
                        columnList = "model_name, horizon_months"
                )
        }
)
@Getter
@Setter
@NoArgsConstructor
public class ModelComparison {

    @EmbeddedId
    private ModelComparisonId id;

    private Double mae;
    private Double mape;
    private Double rmse;
    private Double mse;

    @Column(name = "r2")
    private Double r2;

    @CreationTimestamp
    @Column(name = "evaluated_at", updatable = false)
    private OffsetDateTime evaluatedAt;
}
