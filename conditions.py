import numpy

def getVariables(object, mesh):
    variables = {}
    for mask in object.selection_masks:
        if mask.type == "VERTEX_GROUP":
            variables[mask.name] = inVertexGroup(object, mask.vertexGroupName,
                                                         mask.invert)
        if mask.type == "IN_RANGE":
            if mask.rangetype == "MIN_MAX":
                variables[mask.name] = verticesInRange(mesh, mask.minVector,
                                                             mask.maxVector,
                                                             mask.invert)
            else:
                variables[mask.name] = verticesInRangeCenter(mesh, mask.centerVector,
                                                                   mask.scaleVector,
                                                                   mask.invert)
    return variables

def inVertexGroup(object, name, invert):
    vertexGroup = object.vertex_groups[name]
    verticesCount = len(object.data.vertices)
    weights = numpy.full(verticesCount, False)
    for i in range(verticesCount):
        try: weights[i] = (True, vertexGroup.weight(i))[0]
        except: pass
    return ~weights if invert else weights

def verticesInRange(mesh, min, max, invert):
    result = numpy.full(len(mesh.verts), False)
    for i, vert in enumerate(mesh.verts):
        co = vert.co
        if ((co.x >= min.x) and (co.y >= min.y) and (co.z >= min.z) and
            (co.x <= max.x) and (co.y <= max.y) and (co.z <= max.z)):
            result[i] = True
    return ~result if invert else result

def verticesInRangeCenter(object, center, scale, invert):
    return verticesInRange(object, center - scale, center + scale, invert)
