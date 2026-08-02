package Model.Target;

import Model.Dependency.CellsDTO;
import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
@NoArgsConstructor
@Data
public class TargetModel {
    @SerializedName("@schemaVersion")
    private String schemaVersion;
    @SerializedName("name")
    private String name;
    @SerializedName("variables")
    private List<String> variables;
    @SerializedName("cells")
    private List<CellsDTO> cells;
}
