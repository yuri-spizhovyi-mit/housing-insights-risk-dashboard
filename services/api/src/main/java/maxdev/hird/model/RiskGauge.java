package maxdev.hird.model;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(
        name = "risk_predictions",
        indexes = {
                @Index(
                        name = "idx_risk_city_type_date",
                        columnList = "city, risk_type, predict_date"
                )
        }
)
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RiskGauge {

    @Id
    @GeneratedValue
    @Column(name = "run_id")
    private UUID id;

    private String city;

    @Column(name = "risk_type")
    private String riskType;

    @Column(name = "risk_value")
    private Double riskValue;

    @Column(name = "predict_date")
    private LocalDate predictDate;
}

