package Model.Reflexion;

import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;

@NoArgsConstructor
@Data
public class StructureDTO {
    @SerializedName("@type")
    private String type;
    @SerializedName("name")
    private String name;
    @SerializedName("rawName")
    private String rawName;
    @SerializedName("nested")
    List<StructureDTO> nested;

}
