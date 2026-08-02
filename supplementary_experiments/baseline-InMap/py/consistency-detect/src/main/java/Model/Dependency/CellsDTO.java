package Model.Dependency;

import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
@NoArgsConstructor
@Data
public class CellsDTO {
    @SerializedName("src")
    private Integer src;
    @SerializedName("dest")
    private Integer dest;
    @SerializedName("values")
    private ValuesDTO values;
    @SerializedName("details")
    private List<DetailsDTO> details;
}
