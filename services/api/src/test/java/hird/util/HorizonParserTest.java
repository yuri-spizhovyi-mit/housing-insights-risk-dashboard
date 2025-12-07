package hird.util;

import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

public class HorizonParserTest {
    @Test
    public void testHorizonToMonths(){
        assertEquals(12, HorizonParser.toMonths("1y"));
        assertEquals(24, HorizonParser.toMonths("2y"));
        assertEquals(60, HorizonParser.toMonths("5y"));
        assertEquals(120, HorizonParser.toMonths("10y"));
    }

    @Test
    public void testInvalidHorizon(){
        assertThrows(
                IllegalArgumentException.class,
                () -> HorizonParser.toMonths("25y")
        );
    }
}
