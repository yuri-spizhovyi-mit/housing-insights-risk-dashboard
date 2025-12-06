package hird.model;

import jakarta.persistence.*;
import lombok.*;

import java.time.LocalDate;
import java.util.UUID;

@Entity
@Table(name = "risk_predictions")
@Data
@NoArgsConstructor
@AllArgsConstructor
@Builder
public class RiskGauge {

    @Id
    @GeneratedValue
    private UUID run_id;

    private String city;

    @Column(name = "risk_type")
    private String riskType;

    @Column(name = "risk_value")
    private Double riskValue;

    @Column(name = "predict_date")
    private LocalDate predictDate;
}
