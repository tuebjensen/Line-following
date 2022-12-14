import { createCounter } from './create-counter.js'
import { getPossibleLineSegmentsFromNode } from './possible-line-segments-from-node.js'

/**
 * A function used as the argument of the Array.protoype.sort function
 * if one wants to put numbers in ascending order.
 * @param {number} a The first number.
 * @param {number} b The second number.
 * @returns A negative number if a < b, 0 if a == b and a positive number when a > b.
 */
function asc (a, b) {
    return a - b
}

/**
 * A node.
 * @typedef {{ x: number, y: number, id: number }} Node
 */

/**
 * A line segment.
 * @typedef {{ start: Node, end: Node }} LineSegment
 */

/**
 * Note that the end point is only used to signify
 * the direction of the ray.
 * @typedef {LineSegment} Ray
 */

/**
 * Get the distance between the starting point of the ray and
 * the intersection between the ray and the line segment.
 * @param {Ray} ray
 * @param {LineSegment} segment 
 * @returns {number}
 */
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
        const [minY, maxY] = [segment.start.y, segment.end.y].sort(asc)
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
            throw new Error('The newly created line segment would lay on an other line segment.')
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
            throw new Error('The newly created line segment would lay on an other line segment.')
        }
    }
}

/**
 * @typedef {{ lineSegments: LineSegment[], nodes: Node[] }} Graph
 */

/**
 * Parses the given string.
 * @param {string} str The raw string of the map which should be parsed.
 * @returns {Graph} The parsed map.
 */
export function parseMap (str) {
    const lineSegments = []
    const nodeIdIterator = createCounter()
    const nodes = [{x: 0, y: 0, id: nodeIdIterator.next().value}]
    
    /**
     * Get the node corresponding to the given coordinates.
     * @param {number} x 
     * @param {number} y 
     * @returns {Node}
     */
    function findNode(x, y){
        return nodes.find(node => node.x === x && node.y === y)
    }
   
    /**
     * Parses the remaining part of the map and populates lineSegments and nodes.
     * The arguments define the starting position of the internal cursor.
     * @param {number} startX 
     * @param {number} startY 
     * @returns {void}
     */
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
                const lineSegmentsMapped = lineSegments.map((lineSegment) => getIntersectionDistance(ray, lineSegment))
                const smallestDistance = Math.min(...(lineSegmentsMapped))
                const smallestDistanceIndex = lineSegmentsMapped.indexOf(smallestDistance)

                if (distanceStr === '*' && smallestDistance === Infinity){
                    throw new Error('The newly created line segment would go to infinity.')
                } else if (distanceStr !== '*' && smallestDistance < distance) {
                    throw new Error('The newly created line segment would cross an other line segment.')
                }

                const finalDistance = distanceStr === '*' ? smallestDistance : distance
                const newCurrentX = (direction === 'l' ? -finalDistance : direction === 'r' ? finalDistance : 0) + currentX
                const newCurrentY = (direction === 't' ? -finalDistance : direction === 'b' ? finalDistance : 0) + currentY

                const endNode = nodes.find(node => node.x === newCurrentX && node.y === newCurrentY) || (function(){
                    const newNode = {x: newCurrentX, y: newCurrentY, id: nodeIdIterator.next().value}
                    nodes.push(newNode)
                    if (smallestDistance == finalDistance){
                        const oldEndNode = lineSegments[smallestDistanceIndex].end
                        lineSegments[smallestDistanceIndex].end = newNode
                        const newLineSegment = {
                            start: newNode,
                            end: oldEndNode
                        }
                        lineSegments.push(newLineSegment)
                    }
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
            } else if (/\s/.test(str[0])) {
                str = str.slice(1)
            } else if (/#/.test(str[0])) {
                const commentEnd = str.indexOf('\n')
                if (commentEnd === -1) {
                    str = ''
                    return
                }
                str = str.slice(commentEnd + 1)
            } else {
                throw new Error('Unknown token: ' + str[0])
            }
        }
    }
    _parseMap(0, 0)

    // automatically mark dead-end nodes as destinations
    for (const node of nodes) {
        console.log(getPossibleLineSegmentsFromNode(lineSegments, node))
        node.isPossibleDestination = getPossibleLineSegmentsFromNode(lineSegments, node.id).length <= 1
    }

    return { lineSegments, nodes }
}
