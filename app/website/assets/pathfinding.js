
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
    const parentArray = new Array()
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
           graphline += ' '
        }
        graphline += '\n'
    }
    console.log(graphline)

}

function isInShortestPath(parentArray, target){
    return parentArray.find(node => node == target)
}

export function findPath(map, source, target) {
    // strings used for test:
    //r1t2r3(t4|b5)r6(t5|b5(l2|r4))
    //r1t2r3(t4|b5)r6(t5|b5(l2|r4))r3b2l*
    //r1t2r3(t4|b5r2t2r8)r1r1r1r1r1r1(t5|b*b2(l2|r4))
    const lineSegments = map.lineSegments
    //const lineSegments = map.lineSegments.filter(lineSegment => !(lineSegment.start.id === 3 && lineSegment.end.id === 6)) //NOT CORRECT JUST FOR TEST
    const nodes = map.nodes
    const adjacencyMatrix = makeAdjacencyMatrix(lineSegments, nodes.length)
    const sptParentArray = dijkstra(adjacencyMatrix, source)
    console.log(sptParentArray)
    console.log(target)
    if (!isInShortestPath(sptParentArray, target)) {
        throw new Error('Target is not present in map')
    }
    
    
    const pathFromSourceToTarget = [target]
    let foundPath = false
    let newTarget = target
    while (!foundPath) {
        newTarget = sptParentArray[newTarget]
        if (newTarget === -1) {
            foundPath = true
        } else {
            pathFromSourceToTarget.push(newTarget)
        }
    }

    return pathFromSourceToTarget.reverse()
    
}