package maxdev.hird.controller;


import maxdev.hird.dto.ModelComparisonResponse;
import maxdev.hird.service.ModelComparisonService;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Controller;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;

@Controller
@RequestMapping("/model-comparison")
public class ModelComparisonController {
    private final ModelComparisonService modelComparisonService;

    public ModelComparisonController(ModelComparisonService modelComparisonService){
        this.modelComparisonService = modelComparisonService;
    }

    @GetMapping
    public ResponseEntity<ModelComparisonResponse> getModelComparison(
            @RequestParam String city,
            @RequestParam String target
    ){
        ModelComparisonResponse response = modelComparisonService.retrieveComparisonData(city, target);
        return ResponseEntity.ok(response);
    }
}
