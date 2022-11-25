import { possibleLineSegmentsFromNode } from "./possible-line-segments-from-node.js"

function lengthOfLineSegment(lineSegment) {
    return Math.sqrt((lineSegment.start.x - lineSegment.end.x)**2 + (lineSegment.start.y - lineSegment.end.y)**2)
}

function makeAdjacencyMatrix(lineSegments, numberOfNodes) {
    const adjacencyMatrix = Array(numberOfNodes).fill(0).map(() => Array(numberOfNodes).fill(0))

    for (let i = 0; i < lineSegments.length; i++){
        let lineSegment = lineSegments[i]
        let length = lengthOfLineSegment(lineSegment)
        let startNodeId = lineSegment.start.id
        let endNodeId = lineSegment.end.id
        adjacencyMatrix[startNodeId][endNodeId] = length
        adjacencyMatrix[endNodeId][startNodeId] = length
    }
    return adjacencyMatrix

}

function minDistance(dist, sptSet) {
    let min = Infinity
    let minIndex = -1

    for (let v = 0; v < sptSet.length; v++){
        if (sptSet[v] === false && dist[v] <= min){
            min = dist[v]
            minIndex = v
        }
    }

    return minIndex
}
function printSolution(dist)
{
    console.log("Vertex \t\t Distance from Source<br>");
    for(let i = 0; i < dist.length; i++)
    {
        console.log(i + " \t\t " +
                 dist[i] + "<br>");
    }
}
function dijkstra(graph, src) {
    //Array to store the array representation of the SPT (shortest path tree) 
    //Where the index is the id of the node and the element at that index is the preceding node in the SPT 
    const parentArray = []
    //Array to store distances
    const dist = new Array(graph.length) 
    //Array to store vertices in the SPT
    const sptSet = new Array(graph.length)

    for (let i = 0; i < graph.length; i++){
        dist[i] = Infinity
        sptSet[i] = false
    }

    dist[src] = 0
    parentArray[src] = -1
    for (let i = 0; i < graph.length - 1; i++){
        let u = minDistance(dist, sptSet)
        sptSet[u] = true

        for (let v = 0; v < graph.length; v++) {
            if (!sptSet[v] && graph[u][v] != 0 && dist[u] != Infinity && dist[u] + graph[u][v] < dist[v]){
                dist[v] = dist[u] + graph[u][v]
                parentArray[v] = u 
            }
        }
    }
    return parentArray
}
function printGraph(graph) {
    let graphline = ""
    for (let i = 0; i < graph.length; i++) {
       for (let j = 0; j < graph[i].length; j++) {
           graphline += graph[i][j]
           graphline += " "
        }
        graphline += '\n'
    }
    console.log(graphline)

}

function isLineSegmentOnPath(lineSegment, startNodeId, endNodeId){
    return (lineSegment.start.id === startNodeId && lineSegment.end.id === endNodeId || lineSegment.start.id === endNodeId && lineSegment.end.id === startNodeId)
}

function directionFromLineSegment(startNode, endNode) {

    const direction = {x: 0, y: 0}
    if ((endNode.x - startNode.x) < 0) {
        direction.x = -1
        direction.y = 0
    } else if ((endNode.x - startNode.x) > 0) {
        direction.x = 1
        direction.y = 0
    } else if ((endNode.y - startNode.y) < 0) {
        direction.x = 0
        direction.y = -1
    } else if ((endNode.y - startNode.y) > 0){
        direction.x = 0
        direction.y = 1
    }

    return direction

}

    function cross(v, w) {
        //returns the z component of the cross product
        return (v.x * w.y) - (v.y * w.x)
    }
    function dot(v, w) {
        return (v.x * w.x) + (v.y * w.y)
    }

    function directionToGo(v, w){
        if ((v.x === 0 && v.y === 0) || (w.x === 0 && w.y === 0)){
            throw new Error('vector bad')
        }
        const crossProduct = cross(v, w)
        const dotProduct = dot(v, w) 
        if (dotProduct === 0) {
            if (crossProduct === 1) {
                return "right"
            } else {
                return "left"
            }
        } else if (dotProduct < 0){
            return "straight"
        } else {
            return "back"
        }
    }


function generatePathObject(pathIds, lineSegments, nodes) {
    const pathFromSourceToTarget = []
    let orientation = null
    let lastNodeId = null
    for (let i = 0; i < pathIds.length - 1; i++) {
        let possibilities = []
        let choose = ""
        let nodeId = pathIds[i]
        let nextNodeId = pathIds[i + 1]
        let possibleLineSegments = possibleLineSegmentsFromNode(lineSegments, nodeId)        
        if (orientation == null) {
            for (let j = 0; j < possibleLineSegments.length; j++){

                if (isLineSegmentOnPath(possibleLineSegments[j], nodeId, nextNodeId)) {
                    orientation = directionFromLineSegment(nodes[nodeId], nodes[nextNodeId])
                }
            }
        } else {
            orientation = directionFromLineSegment(nodes[lastNodeId], nodes[nodeId])
        }

        for (let j = 0; j < possibleLineSegments.length; j++){
            let possibleLineSegment = possibleLineSegments[j]
            let possibleNodeId = nodeId === possibleLineSegment.start.id ? possibleLineSegment.end.id : possibleLineSegment.start.id
            let direction = directionFromLineSegment(nodes[nodeId], nodes[possibleNodeId])
            let instruction = directionToGo(orientation, direction)
            possibilities.push(instruction)
            if (isLineSegmentOnPath(possibleLineSegment, nodeId, nextNodeId)) {
                choose = instruction
            }
            
        }
        lastNodeId = nodeId
        pathFromSourceToTarget.push({possibilities: possibilities, choose: choose, nodeId: nodeId})
    }
    pathFromSourceToTarget.push({possibilities: [], choose: "", nodeId: pathIds[pathIds.length - 1]})
    console.log(pathFromSourceToTarget)
    return pathFromSourceToTarget
}

export function findPath(map, source, target) {
    // strings used for test:
    //r1t2r3(t4|b5)r6(t5|b5(l2|r4))
    //r1t2r3(t4|b5)r6(t5|b5(l2|r4))r3b2l*
    //_r1_t2_r3_(t4_|b5_r2_t2_r8_)r6_(t5_|b*_b2_(l2_|r4_))
    const lineSegments = map.lineSegments
    //const lineSegments = map.lineSegments.filter(lineSegment => !(lineSegment.start.id === 3 && lineSegment.end.id === 6)) //NOT CORRECT JUST FOR TEST
    const nodes = map.nodes
    const adjacencyMatrix = makeAdjacencyMatrix(lineSegments, nodes.length)
    const sptParentArray = dijkstra(adjacencyMatrix, source)
    console.log(sptParentArray)

    
    const pathIds = [target]
    let foundPath = false
    let newTarget = target
    while (!foundPath) {
        newTarget = sptParentArray[newTarget]
        if (newTarget === -1) {
            foundPath = true
        } else if (sptParentArray[newTarget] == newTarget){
            throw new Error('Target is not present in map')
        } else {
            pathIds.push(newTarget)
        }
    }

    pathIds.reverse()
    console.log(pathIds)
    return generatePathObject(pathIds, lineSegments, nodes)

}