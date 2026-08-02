package Model.Dependency;

import com.google.gson.annotations.SerializedName;
import lombok.Data;
import lombok.NoArgsConstructor;

@NoArgsConstructor
@Data
public class IndicesDTO {
    @SerializedName("object")
    private String object;
    @SerializedName("file")
    private String file;
    @SerializedName("location")
    private LocationDTO location;
    @SerializedName("type")
    private String type;
    @SerializedName("rawType")
    private String rawType;
    private String extendClassType;
    private String extendVarType;

    private Boolean isOverride;
    private Boolean isSetter;
    private Boolean isGetter;
    private Boolean isDelegator;
    private Boolean isRecursive;
    private Boolean isPublic;
    private Boolean isStatic;
    private Boolean isAssign;
    private Boolean isSynchronized;
    private Boolean isConstructor;
    private Boolean isCallSuper;
    private Boolean methodIsAbstract;
    private Boolean typeIsAbstract;
}
