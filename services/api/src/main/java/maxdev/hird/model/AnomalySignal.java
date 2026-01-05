package maxdev.hird.model;

import jakarta.persistence.*;
import lombok.*;
import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(
        name = "anomaly_signals",
        indexes = {
                @Index(name = "idx_anom_city_target_date", columnList = "city, target, detect_date")
        }
)
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class AnomalySignal {
    @Id
    @GeneratedValue
    @Column(name = "run_id")
    private UUID id;

    private String city;
    private String target;

    @Column(name = "detect_date")
    private LocalDate detectDate;

    @Column(name = "anomaly_score")
    private Double anomalyScore;

    @Column(name = "is_anomaly")
    private Boolean isAnomaly;
}
