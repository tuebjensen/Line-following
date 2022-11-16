
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
    //Array with MST
    const parent = new Array()
    //Array to store distances
    const dist = new Array(graph.length) 
    //Array to store vertices in the MST
    const sptSet = new Array(graph.length)

    for (let i = 0; i < graph.length; i++){
        dist[i] = Infinity
        sptSet[i] = false
    }
    dist[src] = 0
    parent[src] = -1
    for (let i = 0; i < graph.length - 1; i++){
        let u = minDistance(dist, sptSet)
        sptSet[u] = true

        for (let v = 0; v < graph.length; v++) {
            if (!sptSet[v] && graph[u][v] != 0 && dist[u] != Infinity && dist[u] + graph[u][v] < dist[v]){
                dist[v] = dist[u] + graph[u][v]
                parent[v] = u 
            }
        }
    }
    console.log(parent)
    return parent
}
function printGraph(graph) {
    let graphline = ""
    for (let i = 0; i < graph.length; i++) {
       for (let j = 0; j < graph[i].length; j++) {
           graphline += graph[i][j]
           graphline += ' '
        }
        graphline += '\n'
    }
    console.log(graphline)

}

function isInMap(nodes, source, target){
    return nodes.find(node => node.id == source) && nodes.find(node => node.id == target) 
}

export function findPath(map, source, target) {
    //r1t2r3(t4|b5)r6(t5|b5(l2|r4))r3t2l* string used for tests
    const lineSegments = map.lineSegments
    const nodes = map.nodes

    if (!isInMap(nodes, source, target)){
        throw new Error('The source or the target are invalid for this map')   
    }

    const adjacencyMatrix = makeAdjacencyMatrix(lineSegments, nodes.length)
    const sptParent = dijkstra(adjacencyMatrix, source)
    const pathFromSourceToTarget = [target]
    let foundPath = false
    let newTarget = target
    while (!foundPath) {
        newTarget = sptParent[newTarget]
        if (newTarget === -1) {
            foundPath = true
        } else {
            pathFromSourceToTarget.push(newTarget)
        }
    }

    return pathFromSourceToTarget.reverse()
    
}