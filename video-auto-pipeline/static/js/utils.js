// 通用工具函数

// API请求封装
async function apiRequest(url, options = {}) {
    const defaultOptions = {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
        },
    };
    
    const config = { ...defaultOptions, ...options };
    
    if (config.body && typeof config.body === 'object') {
        config.body = JSON.stringify(config.body);
    }
    
    try {
        const response = await fetch(url, config);
        
        if (!response.ok) {
            const errorData = await response.json().catch(() => ({}));
            throw new Error(errorData.message || `HTTP ${response.status}: ${response.statusText}`);
        }
        
        const contentType = response.headers.get('content-type');
        if (contentType && contentType.includes('application/json')) {
            return await response.json();
        }
        
        return await response.text();
    } catch (error) {
        console.error('API请求失败:', error);
        throw error;
    }
}

// 显示通知
function showNotification(message, type = 'info', duration = 5000) {
    const notification = document.createElement('div');
    notification.className = `alert alert-${type} notification`;
    notification.innerHTML = `
        <div class="d-flex justify-content-between align-items-center">
            <div>
                <i class="fas fa-${getNotificationIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close" onclick="this.parentElement.parentElement.remove()"></button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // 自动移除通知
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, duration);
}

// 获取通知图标
function getNotificationIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-circle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// 确认操作对话框
function confirmAction(message, callback, title = '确认操作') {
    const modal = document.createElement('div');
    modal.className = 'modal fade';
    modal.innerHTML = `
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">${title}</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                </div>
                <div class="modal-body">
                    <p>${message}</p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">取消</button>
                    <button type="button" class="btn btn-danger" id="confirmBtn">确认</button>
                </div>
            </div>
        </div>
    `;
    
    document.body.appendChild(modal);
    
    const bootstrapModal = new bootstrap.Modal(modal);
    bootstrapModal.show();
    
    modal.querySelector('#confirmBtn').addEventListener('click', () => {
        callback();
        bootstrapModal.hide();
    });
    
    modal.addEventListener('hidden.bs.modal', () => {
        modal.remove();
    });
}

// 格式化文件大小
function formatFileSize(bytes) {
    if (bytes === 0) return '0 B';
    
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// 格式化时长（秒转换为时:分:秒）
function formatDuration(seconds) {
    if (!seconds || seconds < 0) return '00:00';
    
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (hours > 0) {
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    } else {
        return `${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }
}

// 格式化日期
function formatDate(dateString, includeTime = true) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    // 如果是今天
    if (diffDays === 1) {
        if (includeTime) {
            return '今天 ' + date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
        } else {
            return '今天';
        }
    }
    
    // 如果是昨天
    if (diffDays === 2) {
        if (includeTime) {
            return '昨天 ' + date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
        } else {
            return '昨天';
        }
    }
    
    // 如果是本年
    if (date.getFullYear() === now.getFullYear()) {
        if (includeTime) {
            return date.toLocaleDateString('zh-CN', {month: 'short', day: 'numeric'}) + ' ' + 
                   date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
        } else {
            return date.toLocaleDateString('zh-CN', {month: 'short', day: 'numeric'});
        }
    }
    
    // 其他情况
    if (includeTime) {
        return date.toLocaleDateString('zh-CN') + ' ' + 
               date.toLocaleTimeString('zh-CN', {hour: '2-digit', minute: '2-digit'});
    } else {
        return date.toLocaleDateString('zh-CN');
    }
}

// 格式化相对时间
function formatRelativeTime(dateString) {
    if (!dateString) return '-';
    
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = now - date;
    const diffMinutes = Math.floor(diffTime / (1000 * 60));
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffMinutes < 1) {
        return '刚刚';
    } else if (diffMinutes < 60) {
        return `${diffMinutes}分钟前`;
    } else if (diffHours < 24) {
        return `${diffHours}小时前`;
    } else if (diffDays < 7) {
        return `${diffDays}天前`;
    } else {
        return formatDate(dateString, false);
    }
}

// 格式化数字（添加千分位分隔符）
function formatNumber(num) {
    if (typeof num !== 'number') return '0';
    
    if (num >= 100000000) {
        return (num / 100000000).toFixed(1) + '亿';
    } else if (num >= 10000) {
        return (num / 10000).toFixed(1) + '万';
    } else if (num >= 1000) {
        return (num / 1000).toFixed(1) + 'k';
    }
    
    return num.toLocaleString('zh-CN');
}

// 防抖函数
function debounce(func, wait, immediate) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            timeout = null;
            if (!immediate) func(...args);
        };
        const callNow = immediate && !timeout;
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
        if (callNow) func(...args);
    };
}

// 节流函数
function throttle(func, limit) {
    let inThrottle;
    return function(...args) {
        if (!inThrottle) {
            func.apply(this, args);
            inThrottle = true;
            setTimeout(() => inThrottle = false, limit);
        }
    };
}

// 深拷贝对象
function deepClone(obj) {
    if (obj === null || typeof obj !== 'object') return obj;
    if (obj instanceof Date) return new Date(obj.getTime());
    if (obj instanceof Array) return obj.map(item => deepClone(item));
    if (typeof obj === 'object') {
        const clonedObj = {};
        for (const key in obj) {
            if (obj.hasOwnProperty(key)) {
                clonedObj[key] = deepClone(obj[key]);
            }
        }
        return clonedObj;
    }
}

// 生成随机ID
function generateId(length = 8) {
    const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    let result = '';
    for (let i = 0; i < length; i++) {
        result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
}

// 验证邮箱格式
function validateEmail(email) {
    const re = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return re.test(email);
}

// 验证URL格式
function validateUrl(url) {
    try {
        new URL(url);
        return true;
    } catch {
        return false;
    }
}

// 获取URL参数
function getUrlParameter(name) {
    const urlParams = new URLSearchParams(window.location.search);
    return urlParams.get(name);
}

// 设置URL参数
function setUrlParameter(name, value) {
    const url = new URL(window.location);
    url.searchParams.set(name, value);
    window.history.pushState({}, '', url);
}

// 移除URL参数
function removeUrlParameter(name) {
    const url = new URL(window.location);
    url.searchParams.delete(name);
    window.history.pushState({}, '', url);
}

// 复制文本到剪贴板
async function copyToClipboard(text) {
    try {
        await navigator.clipboard.writeText(text);
        showNotification('已复制到剪贴板', 'success', 2000);
        return true;
    } catch (err) {
        console.error('复制失败:', err);
        showNotification('复制失败', 'error', 2000);
        return false;
    }
}

// 下载文件
function downloadFile(url, filename) {
    const link = document.createElement('a');
    link.href = url;
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// 上传文件
function uploadFile(file, url, onProgress, onSuccess, onError) {
    const formData = new FormData();
    formData.append('file', file);
    
    const xhr = new XMLHttpRequest();
    
    xhr.upload.addEventListener('progress', (e) => {
        if (e.lengthComputable && onProgress) {
            const percentComplete = (e.loaded / e.total) * 100;
            onProgress(percentComplete);
        }
    });
    
    xhr.addEventListener('load', () => {
        if (xhr.status === 200) {
            try {
                const response = JSON.parse(xhr.responseText);
                if (onSuccess) onSuccess(response);
            } catch (e) {
                if (onSuccess) onSuccess(xhr.responseText);
            }
        } else {
            if (onError) onError(new Error(`上传失败: ${xhr.status}`));
        }
    });
    
    xhr.addEventListener('error', () => {
        if (onError) onError(new Error('网络错误'));
    });
    
    xhr.open('POST', url);
    xhr.send(formData);
}

// 检查网络连接状态
function checkNetworkStatus() {
    return navigator.onLine;
}

// 监听网络状态变化
function onNetworkStatusChange(callback) {
    window.addEventListener('online', () => callback(true));
    window.addEventListener('offline', () => callback(false));
}

// 获取设备信息
function getDeviceInfo() {
    return {
        userAgent: navigator.userAgent,
        platform: navigator.platform,
        language: navigator.language,
        cookieEnabled: navigator.cookieEnabled,
        onLine: navigator.onLine,
        screenWidth: screen.width,
        screenHeight: screen.height,
        windowWidth: window.innerWidth,
        windowHeight: window.innerHeight
    };
}

// 本地存储封装
const storage = {
    set(key, value, expiry = null) {
        const item = {
            value: value,
            expiry: expiry ? Date.now() + expiry : null
        };
        localStorage.setItem(key, JSON.stringify(item));
    },
    
    get(key) {
        const itemStr = localStorage.getItem(key);
        if (!itemStr) return null;
        
        try {
            const item = JSON.parse(itemStr);
            if (item.expiry && Date.now() > item.expiry) {
                localStorage.removeItem(key);
                return null;
            }
            return item.value;
        } catch (e) {
            localStorage.removeItem(key);
            return null;
        }
    },
    
    remove(key) {
        localStorage.removeItem(key);
    },
    
    clear() {
        localStorage.clear();
    }
};

// 会话存储封装
const sessionStorage = {
    set(key, value) {
        window.sessionStorage.setItem(key, JSON.stringify(value));
    },
    
    get(key) {
        const itemStr = window.sessionStorage.getItem(key);
        if (!itemStr) return null;
        
        try {
            return JSON.parse(itemStr);
        } catch (e) {
            window.sessionStorage.removeItem(key);
            return null;
        }
    },
    
    remove(key) {
        window.sessionStorage.removeItem(key);
    },
    
    clear() {
        window.sessionStorage.clear();
    }
};

// 事件总线
class EventBus {
    constructor() {
        this.events = {};
    }
    
    on(event, callback) {
        if (!this.events[event]) {
            this.events[event] = [];
        }
        this.events[event].push(callback);
    }
    
    off(event, callback) {
        if (!this.events[event]) return;
        
        const index = this.events[event].indexOf(callback);
        if (index > -1) {
            this.events[event].splice(index, 1);
        }
    }
    
    emit(event, data) {
        if (!this.events[event]) return;
        
        this.events[event].forEach(callback => {
            try {
                callback(data);
            } catch (e) {
                console.error('事件处理器执行错误:', e);
            }
        });
    }
    
    once(event, callback) {
        const onceCallback = (data) => {
            callback(data);
            this.off(event, onceCallback);
        };
        this.on(event, onceCallback);
    }
}

// 全局事件总线实例
const eventBus = new EventBus();

// 页面加载完成后的初始化
document.addEventListener('DOMContentLoaded', function() {
    // 初始化工具提示
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });
    
    // 初始化弹出框
    const popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });
    
    // 监听网络状态
    onNetworkStatusChange((isOnline) => {
        if (isOnline) {
            showNotification('网络连接已恢复', 'success', 3000);
        } else {
            showNotification('网络连接已断开', 'warning', 5000);
        }
    });
    
    // 全局错误处理
    window.addEventListener('error', (e) => {
        console.error('全局错误:', e.error);
        showNotification('发生了一个错误，请刷新页面重试', 'error');
    });
    
    // 全局未处理的Promise拒绝
    window.addEventListener('unhandledrejection', (e) => {
        console.error('未处理的Promise拒绝:', e.reason);
        showNotification('操作失败，请重试', 'error');
    });
});

// 导出工具函数（如果使用模块系统）
if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
        apiRequest,
        showNotification,
        confirmAction,
        formatFileSize,
        formatDuration,
        formatDate,
        formatRelativeTime,
        formatNumber,
        debounce,
        throttle,
        deepClone,
        generateId,
        validateEmail,
        validateUrl,
        getUrlParameter,
        setUrlParameter,
        removeUrlParameter,
        copyToClipboard,
        downloadFile,
        uploadFile,
        checkNetworkStatus,
        onNetworkStatusChange,
        getDeviceInfo,
        storage,
        sessionStorage,
        EventBus,
        eventBus
    };
}