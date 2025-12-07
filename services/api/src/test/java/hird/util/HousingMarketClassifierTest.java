package hird.util;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class HousingMarketClassifierTest {

    @Test
    void testAffordabilityMapping() {
        assertEquals("Tight", HousingMarketClassifier.mapAffordability(0.85));
        assertEquals("Moderate", HousingMarketClassifier.mapAffordability(0.60));
        assertEquals("Comfortable", HousingMarketClassifier.mapAffordability(0.30));
    }

    @Test
    void testPriceToRentMapping() {
        assertEquals("Elevated", HousingMarketClassifier.mapPriceToRent(0.75));
        assertEquals("Balanced", HousingMarketClassifier.mapPriceToRent(0.50));
        assertEquals("Attractive", HousingMarketClassifier.mapPriceToRent(0.20));
    }

    @Test
    void testInventoryMapping() {
        assertEquals("Low", HousingMarketClassifier.mapInventory(0.2));
        assertEquals("Adequate", HousingMarketClassifier.mapInventory(0.5));
        assertEquals("High", HousingMarketClassifier.mapInventory(0.9));
    }
}
