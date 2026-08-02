package Model.Reflexion;

import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
@NoArgsConstructor
@Data
public class ReflectionModel {
    @SerializedName("@schemaVersion")
    private String schemaVersion;
    @SerializedName("name")
    private String name;
    @SerializedName("structure")
    private List<StructureDTO> structure;
}
