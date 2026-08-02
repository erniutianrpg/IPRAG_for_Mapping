package Model.Dependency;

import java.util.List;
import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class DependencyData {
    @SerializedName("name")
    private String name;
    @SerializedName("lang")
    private String lang;
    @SerializedName("rootDir")
    private String rootDir;
    @SerializedName("nodeNum")
    private Integer nodeNum;
    @SerializedName("edgeNum")
    private Integer edgeNum;
    @SerializedName("cells")
    private List<CellsDTO> cells;
    @SerializedName("variables")
    private List<String> variables;
    @SerializedName("indices")
    private List<IndicesDTO> indices;
    @SerializedName("indexNum")
    private Integer indexNum;
}
