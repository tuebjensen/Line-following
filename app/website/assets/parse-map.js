function asc (a, b) {
    return a - b
}

function getIntersectionDistance (ray, segment) {
    const isVert1 = ray.start.x === ray.end.x
    const isVert2 = segment.start.x === segment.end.x
    if (isVert1 && !isVert2) {
        const x = ray.start.x
        const y = segment.start.y
        const [minX, maxX] = [segment.start.x, segment.end.x].sort(asc)
        if (minX <= x && x <= maxX) {
            const distance = (y - ray.start.y) * Math.sign(ray.end.y - ray.start.y)
            if (distance > 0) {
                return distance
            }
        }
        return Infinity 
    } else if (!isVert1 && isVert2) {
        const y = ray.start.y
        const x = segment.start.x
        const [minY, maxY] = [segment.start.y, segment.end.x].sort(asc)
        if (minY <= y && y <= maxY ) {
            const distance = (x - ray.start.x) * Math.sign(ray.end.x - ray.start.x)
            if (distance > 0) {
                return distance
            }
        }
        return Infinity 
    } else if (isVert1 && isVert1) {
        if (ray.start.x !== segment.start.x) {
            return Infinity
        }
        const distance1 = (segment.start.y - ray.start.y) * Math.sign(ray.end.y - ray.start.y)
        const distance2 = (segment.end.y - ray.start.y) * Math.sign(ray.end.y - ray.start.y)
        if (distance1 > 0 && distance2 > 0) {
            return Math.min(distance1, distance2)
        } else if (distance1 <= 0 && distance2 <= 0) {
            return Infinity
        } else {
            console.log(distance1, distance2)
            throw new Error('Eror (vert)')
        }
    } else if (!isVert1 && !isVert2) {
        if (ray.start.y !== segment.start.y) {
            return Infinity
        }
        const distance1 = (segment.start.x - ray.start.x) * Math.sign(ray.end.x - ray.start.x)
        const distance2 = (segment.end.x - ray.start.x) * Math.sign(ray.end.x - ray.start.x)
        if (distance1 > 0 && distance2 > 0) {
            return Math.min(distance1, distance2)
        } else if (distance1 <= 0 && distance2 <= 0) {
            return Infinity
        } else {
            throw new Error('Eror (hori)')
        }
    }
}
function* createGenerateNodeId() {
    for (let i = 0; ; i++) {
        yield i
    }
}
export function parseMap (str) {
    const lineSegments = []
    const nodeIdIterator = createGenerateNodeId()
    const nodes = [{x: 0, y: 0, id: nodeIdIterator.next().value}]
    
    function findNode(x, y){
        return nodes.find(node => node.x === x && node.y === y)
    }
    
    function _parseMap (startX, startY) {
        let currentX = startX, currentY = startY
        while (str.length > 0) {
            if ('trbl'.includes(str[0])) {
                const direction = str[0]
                const distanceStr = str.slice(1).match(/\*|[0-9.]+/)?.[0]
                if (!distanceStr) {
                    throw new Error('distance is formatted incorrectly!')
                }
                const distance = parseFloat(distanceStr) || 1
                const endX = (direction === 'l' ? -distance : direction === 'r' ? distance : 0) + currentX
                const endY = (direction === 't' ? -distance : direction === 'b' ? distance : 0) + currentY                    
                const ray = {start: {x: currentX, y: currentY}, end: {x: endX, y: endY}}
                const smallestDistance = Math.min(...(lineSegments.map((lineSegment) => getIntersectionDistance(ray, lineSegment))))
                if (distanceStr === '*'){
                    if (smallestDistance === Infinity){
                        throw new Error('Eror (something *)')
                    }
                } else {
                    if (smallestDistance < distance){
                        throw new Error('Eror (too long)')
                    }
                }
                const finalDistance = distanceStr === '*' ? smallestDistance : distance
                const newCurrentX = (direction === 'l' ? -finalDistance : direction === 'r' ? finalDistance : 0) + currentX
                const newCurrentY = (direction === 't' ? -finalDistance : direction === 'b' ? finalDistance : 0) + currentY

                const endNode = nodes.find(node => node.x === newCurrentX && node.y === newCurrentY) || (function(){
                    const newNode = {x: newCurrentX, y: newCurrentY, id: nodeIdIterator.next().value}
                    nodes.push(newNode)
                    return newNode
                })()

                const lineSegment = {
                    start: findNode(currentX, currentY),
                    end: endNode
                }
                lineSegments.push(lineSegment)
                currentX = newCurrentX
                currentY = newCurrentY

                str = str.slice(1 + distanceStr.length)
            } else if (str[0] === ')') {
                str = str.slice(1)
                return
            } else if (str[0] === '(') {
                str = str.slice(1)
                _parseMap(currentX, currentY)
            } else if (str[0] === '|') {
                str = str.slice(1)
                currentX = startX
                currentY = startY
            } else if (str[0] === '_') {
                str = str.slice(1)
                const existingNode = findNode(currentX, currentY)
                if (existingNode){
                    existingNode.isPossibleDestination = true
                } else {
                    throw new Error('Eror (no node)')    
                }
            }
        }
    }
    _parseMap(0, 0)

    return { lineSegments, nodes }
}
